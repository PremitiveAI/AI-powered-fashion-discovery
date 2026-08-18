import { NextResponse } from "next/server";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function POST(req: Request) {
  try {
    // Read multipart form-data (image file)
    const formData = await req.formData();

    // Forward request to backend
    const backendRes = await fetch(`${API_URL}product/search`, {
      method: "POST",
      headers: {
        "PK-apiToken": API_TOKEN,
        "PK-role": "User",
        "PK-country": "IN",
        "PK-timezone": "Asia/Kolkata",
        // ❌ DO NOT set Content-Type manually for multipart
      },
      body: formData,
    });

    const contentType = backendRes.headers.get("content-type");

    // Backend may return non-JSON in some cases
    if (!contentType || !contentType.includes("application/json")) {
      return NextResponse.json(
        { success: true },
        { status: backendRes.status }
      );
    }

    const data = await backendRes.json();
    return NextResponse.json(data, { status: backendRes.status });

  } catch (error) {
    console.error("❌ Product search route error:", error);
    return NextResponse.json(
      { message: "Product search failed" },
      { status: 500 }
    );
  }
}
