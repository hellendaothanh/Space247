# Blind reviewer findings — pending combined triage

Review halted before combined triage because fresh reviewer creation failed with `agent thread limit reached` for edge-case and verification-gap layers. These are reviewer claims, not yet independently confirmed verdicts.

1. Loft, pets, or entire-house language can overwrite explicit sale intent with rent.
2. Inferred maximum price can conflict with an explicit minimum and raise an uncaught validation error.
3. Bách Khoa normalization overrides explicitly supplied Ho Chi Minh City with Hanoi.
4. Unresolved landmarks on GET/vector paths drop the location constraint without semantic fallback.
5. Web natural-language results cap at 100 without pagination or a disclosed cap.
6. Pagination uses draft filters rather than the submitted filters.
7. Mobile landmark input only commits on keyboard submission, not the visible search action.
8. Washer and pet negation can be interpreted as positive exact filters.
9. Rental details assume VND while the property contract accepts other currencies.
10. curfew=false with a supplied time displays inconsistently on web and mobile.

Finding floor calculation: 102,830 bytes / 1,024 = 100.42 kB; min(floor(sqrt(100.42) + 1), 10) = 10.
