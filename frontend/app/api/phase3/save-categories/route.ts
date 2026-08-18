import { NextRequest, NextResponse } from "next/server";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const res = await fetch(`${API_URL}cosmetics/save-categories`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json", // 🔥 IMPORTANT
        "PK-apiToken": API_TOKEN,
        "PK-role": "User",
        "PK-country": "IN",
        "PK-timezone": "Asia/Kolkata",
      },
      body: JSON.stringify({
        category_ids: body.category_ids
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      console.error("Backend error:", data);
      return NextResponse.json(
        { message: "Failed to fetch categories", details: data },
        { status: res.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Route error:", error);
    return NextResponse.json(
      { message: "Something went wrong" },
      { status: 500 }
    );
  }
}
