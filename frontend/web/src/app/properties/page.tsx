import { redirect } from "next/navigation";

interface PropertiesPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function PropertiesPage({ searchParams }: PropertiesPageProps) {
  const params = await searchParams;
  const queryString = new URLSearchParams();

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (typeof value === "string") {
        queryString.set(key, value);
      } else if (Array.isArray(value)) {
        value.forEach((v) => queryString.append(key, v));
      }
    }
  }

  if (!queryString.has("listing_type")) {
    queryString.set("listing_type", "sale");
  }

  redirect(`/?${queryString.toString()}`);
}
