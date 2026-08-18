import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { lat, lng } = await req.json();

    // Step 1: Fetch nearby clothing stores
    const nearbyUrl = `https://api.olamaps.io/places/v1/nearbysearch?location=${lat},${lng}&radius=5000&types=clothing_store`;
    const nearbyRes = await fetch(nearbyUrl, {
      method: "GET",
      headers: { "X-API-Key": process.env.NEXT_PUBLIC_OLA_MAPS_API_KEY as string },
    });

    if (!nearbyRes.ok) {
      console.error("❌ Nearby search failed", nearbyRes.status);
      return NextResponse.json({ places: [] });
    }

    const nearbyJson = await nearbyRes.json();
    const predictions = nearbyJson.predictions || [];

    // Step 2: For each prediction, fetch details to get exact lat/lng
    const stores = await Promise.all(
      predictions.map(async (p: any) => {
        try {
          const detailsUrl = `https://api.olamaps.io/places/v1/details?place_id=${p.place_id}`;
          const detailsRes = await fetch(detailsUrl, {
            method: "GET",
            headers: { "X-API-Key": process.env.NEXT_PUBLIC_OLA_MAPS_API_KEY as string },
          });

          if (!detailsRes.ok) return null;

          const detailsJson = await detailsRes.json();
          const location = detailsJson.result?.geometry?.location;

          return location
            ? {
                name: p.structured_formatting.main_text || p.description,
                lat: location.lat,
                lng: location.lng,
                address: p.description,
                distance: Math.round((p.distance_meters || 0) / 1000 * 10) / 10, // km
              }
            : null;
        } catch (error) {
          console.error("❌ Details fetch error:", error);
          return null;
        }
      })
    );

    // Step 3: Filter out nulls and return
    const filteredStores = stores.filter(Boolean);

    return NextResponse.json({ places: filteredStores });
  } catch (error) {
    console.error("❌ Nearby stores route error:", error);
    return NextResponse.json({ places: [] });
  }
}
