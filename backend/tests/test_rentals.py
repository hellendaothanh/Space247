from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import pytest
from fastapi import BackgroundTasks
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import CompileError
from sqlalchemy.dialects import postgresql
from alembic import command
from tests.test_alembic_migrations import get_alembic_config
from src.models.property import Property
from src.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse, PropertySearchQuery, SemanticSearchQuery
from src.schemas.rental import RentalCosts, RentalRules, RentalFilters
from src.schemas.chat import ChatMessage, ExtractedCriteria
from src.services.embedding import EmbeddingService
from src.services.chat_assistant import ChatAssistantService
from src.services.rental import apply_rental_filters, deposit_amount, rental_text, resolve_landmark
from src.api.v1.endpoints.properties import create_property, update_property, search_properties, list_properties
from src.api.v1.endpoints.search import semantic_search


def listing(**changes):
    return dict(title="Phòng trọ sáng", description="Phòng rộng có cửa sổ", property_type="apartment", listing_type="rent", price=3000000, area_sqm=25, address="Đại Cồ Việt", city="Hà Nội", **changes)


def sql(stmt):
    try:
        return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    except CompileError:
        compiled = stmt.compile(dialect=postgresql.dialect())
        rendered = str(compiled)
        for key, value in compiled.params.items():
            rendered = rendered.replace("%(" + key + ")s", repr(value.value if hasattr(value, "value") else value))
        return rendered


@pytest.mark.parametrize("model,data", [(RentalCosts, {"deposit_months": -1}), (RentalCosts, {"electricity_per_kwh": -1}), (RentalCosts, {"electricity_billing": "free"}), (RentalCosts, {"water_unit": "free"}), (RentalCosts, {"service_fee_monthly": float("inf")}), (RentalRules, {"curfew_time": "24:00"}), (RentalRules, {"max_occupants": 0}), (RentalRules, {"max_occupants": 1.2})])
def test_invalid_metadata(model, data):
    with pytest.raises(ValidationError): model.model_validate(data)


def test_enums_zero_false_unknown_and_deposit():
    with pytest.raises(ValidationError): PropertyCreate(**listing(rental_type="hotel"))
    value = PropertyCreate(**listing(rental_type="room", rental_costs={"deposit_months": 0, "service_fee_monthly": 0}, rental_rules={"allow_pets": False}))
    assert value.rental_costs.service_fee_monthly == 0
    assert value.rental_costs.water_cost is None
    assert value.rental_rules.allow_pets is False
    assert deposit_amount(3000000, 2) == Decimal("6000000")
    assert deposit_amount(3000000, 0) == 0
    assert deposit_amount(3000000, None) is None
    legacy = PropertyResponse.model_validate(Property(**listing()))
    assert legacy.rental_costs is None and legacy.rental_rules is None


def test_exact_sql_predicates_and_geography():
    stmt = apply_rental_filters(select(Property), RentalFilters(rental_type="room", allow_pets=False, has_mezzanine=True, max_deposit=0, electricity_billing="state_rate"), (21.0056, 105.8433)).limit(10)
    query = sql(stmt)
    for fragment in ["listing_type = 'rent'", "status = 'active'", "rental_type = 'room'", "allow_pets", "= false", "has_mezzanine", "deposit_months", "<= 0", "state_rate", "ST_DWithin", "3000"]:
        assert fragment in query
    assert "coalesce" not in query.lower()  # Missing keys remain unknown.
    assert query.index("deposit_months") < query.index("LIMIT")


def test_rental_embedding_text():
    text = EmbeddingService().build_property_text("Phòng", "Cho thuê", "Hà Nội", listing_type="rent", rental_type="room", rental_costs={"service_fee_monthly": 0, "water_cost": None}, rental_rules={"allow_pets": False})
    assert "Phòng trọ" in text and "service_fee_monthly): 0" in text and "allow_pets): Không" in text
    assert "water_cost" not in text


def test_chat_rental_intent():
    _, criteria = ChatAssistantService(MagicMock()).parse_intent_and_criteria([ChatMessage(role="user", content="Tìm phòng trọ có gác cho nuôi thú cưng dưới 5 triệu gần Bách Khoa, điện giá nhà nước cọc tối đa 1 tháng")])
    assert criteria.listing_type == "rent" and criteria.rental_type == "room"
    assert criteria.has_mezzanine is True and criteria.allow_pets is True
    assert criteria.max_price == 5000000 and criteria.max_deposit == 1
    assert criteria.electricity_billing == "state_rate" and criteria.near_landmark == "Bách Khoa"


def test_requested_contract_and_original_chat_example():
    from src.schemas.rental import RentalCostSchema, RentalRuleSchema
    costs = dict(deposit_months=1, electricity_per_kwh=3500, water_cost=100000,
                 water_unit="per_person", service_fee_monthly=0, parking_fee_monthly=50000,
                 electricity_billing="state_rate")
    rules = dict(curfew=False, curfew_time=None, allow_pets=True, max_occupants=2,
                 has_mezzanine=True, private_bathroom=True, has_washing_machine=True,
                 live_with_owner=False, has_elevator=True, fingerprint_lock=True)
    assert RentalCostSchema(**costs).model_dump() == costs
    assert RentalRuleSchema(**rules).model_dump() == rules
    with pytest.raises(ValidationError):
        RentalCostSchema(deposit_months=1.5)
    _, criteria = ChatAssistantService(MagicMock()).parse_intent_and_criteria([
        ChatMessage(role="user", content="tìm phòng trọ quanh Bách Khoa có gác lửng dưới 3 triệu điện giá dân")])
    assert criteria.near_landmark == "Bách Khoa"
    assert criteria.rental_type == "room" and criteria.has_mezzanine is True
    assert criteria.max_price == 3000000 and criteria.electricity_billing == "state_rate"
    query = sql(apply_rental_filters(select(Property), RentalFilters(curfew=False, private_bathroom=True)))
    assert "curfew" in query and "private_bathroom" in query and "= false" in query


def test_intent_guards_currency_and_curfew_contract():
    service = ChatAssistantService(MagicMock())
    _, purchase = service.parse_intent_and_criteria([ChatMessage(role="user", content="mua nhà nguyên căn có gác và máy giặt")])
    assert purchase.listing_type == "sale" and purchase.rental_type is None and purchase.has_mezzanine is None
    _, excluded = service.parse_intent_and_criteria([ChatMessage(role="user", content="tìm phòng trọ không có máy giặt, không cho nuôi thú cưng")])
    assert excluded.has_washing_machine is False and excluded.allow_pets is False
    with pytest.raises(ValidationError):
        PropertyCreate(**listing(currency="USD"))
    with pytest.raises(ValidationError):
        RentalRules(curfew=False, curfew_time="23:00")


@pytest.mark.asyncio
async def test_landmark_resolution_and_unavailable_fallback():
    point = await resolve_landmark(RentalFilters(near_landmark="Bách Khoa"))
    assert point == (21.0056, 105.8433)
    with patch("src.services.spatial_service.SpatialService.geocode_landmark", AsyncMock(return_value=None)):
        assert await resolve_landmark(RentalFilters(near_landmark="unknown")) is None


@pytest.mark.asyncio
async def test_create_update_round_trip_clear_and_refresh():
    db = AsyncMock(); db.add = MagicMock()
    user = MagicMock(id=uuid.uuid4(), role="user")
    embedding = EmbeddingService()
    embedding.generate_embedding = MagicMock(return_value=[0.1] * 768)
    with patch("src.api.v1.endpoints.properties.invalidate_property_caches", AsyncMock()) as invalidate:
        prop = await create_property(PropertyCreate(**listing(rental_type="room", rental_costs={"service_fee_monthly": 0, "deposit_months": 1}, rental_rules={"allow_pets": False})), BackgroundTasks(), user, db, embedding)
        assert prop.rental_rules["allow_pets"] is False
        assert PropertyResponse.model_validate(prop).rental_costs.service_fee_monthly == 0
        result = MagicMock(); result.scalar_one_or_none.return_value = prop; db.execute.return_value = result
        embedding.generate_embedding.reset_mock()
        await update_property(prop.id, PropertyUpdate(rental_costs={"deposit_months": 2}), user, db, embedding)
        assert prop.rental_costs["service_fee_monthly"] == 0 and prop.rental_costs["deposit_months"] == 2
        embedding.generate_embedding.assert_called_once()
        assert "deposit_months): 2" in embedding.generate_embedding.call_args.args[0]
        await update_property(prop.id, PropertyUpdate(rental_rules=None), user, db, embedding)
        assert prop.rental_rules is None
        original_title = prop.title
        await update_property(prop.id, PropertyUpdate(listing_type="sale"), user, db, embedding)
        assert prop.rental_type is None and prop.rental_costs is None and prop.rental_rules is None
        assert prop.title == original_title
        assert invalidate.await_count == 4


@pytest.mark.asyncio
async def test_all_search_branches_filter_before_limit():
    db = AsyncMock(); result = MagicMock(); result.all.return_value = []; result.scalars.return_value.all.return_value = []; db.execute.return_value = result
    embedding = MagicMock(); embedding.generate_embedding.return_value = [0.0] * 768
    with patch("src.api.v1.endpoints.properties.get_cached_json", AsyncMock(return_value=None)), patch("src.api.v1.endpoints.properties.set_cached_json", AsyncMock()):
        await search_properties(PropertySearchQuery(query="phòng trọ có gác", allow_pets=False, max_deposit=0), db, embedding)
    assert db.execute.await_count == 2
    for call in db.execute.await_args_list:
        query = sql(call.args[0])
        assert "allow_pets" in query and "deposit_months" in query and "rental_type = 'room'" in query
        assert query.index("allow_pets") < query.index("LIMIT")
    db.execute.reset_mock()
    with patch("src.api.v1.endpoints.search.get_cached_json", AsyncMock(return_value=None)), patch("src.api.v1.endpoints.search.set_cached_json", AsyncMock()):
        await semantic_search(SemanticSearchQuery(query_vector=[0.0] * 768, has_mezzanine=False), db)
    assert "has_mezzanine" in sql(db.execute.call_args.args[0])
    db.execute.reset_mock()
    await list_properties(skip=0, limit=20, listing_type=None, property_type=None, city=None, min_price=0, max_price=5000000, rental=RentalFilters(max_deposit=0), status=None, db=db)
    assert "deposit_months" in sql(db.execute.call_args.args[0])


@pytest.mark.asyncio
async def test_chat_fallback_keeps_exact_filters():
    db = AsyncMock(); result = MagicMock(); result.scalars.return_value.all.return_value = []; result.all.return_value = []
    db.execute.side_effect = [RuntimeError("vector unavailable"), result, result]
    embedding = MagicMock(); embedding.generate_embedding.return_value = [0.0] * 768
    await ChatAssistantService(embedding).execute_hybrid_search(db, ExtractedCriteria(raw_query="phòng", allow_pets=False, max_deposit=0))
    assert len(db.execute.await_args_list) >= 2
    for call in db.execute.await_args_list:
        query = sql(call.args[0]); assert "allow_pets" in query and "deposit_months" in query


def test_migration_upgrade_downgrade_preserves_listing_type(capsys):
    command.upgrade(get_alembic_config(), "0007:0008", sql=True)
    upgrade = capsys.readouterr().out
    assert "ALTER COLUMN listing_type SET DEFAULT 'sale'" in upgrade
    assert "ADD COLUMN listing_type" not in upgrade
    assert "rental_costs JSONB" in upgrade and "rental_rules JSONB" in upgrade
    assert "(listing_type, rental_type, price)" in upgrade
    command.downgrade(get_alembic_config(), "0008:0007", sql=True)
    downgrade = capsys.readouterr().out
    assert "DROP COLUMN rental_costs" in downgrade
    assert "DROP COLUMN listing_type" not in downgrade
