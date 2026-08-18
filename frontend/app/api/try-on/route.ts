import { NextResponse } from "next/server";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();

    const userPhoto = formData.get("user_photo") as File;
    const clothUrl = formData.get("cloth_url") as string;

    if (!userPhoto || !clothUrl) {
      return NextResponse.json({ message: "Missing fields" }, { status: 400 });
    }

    // Send to backend
    const backendForm = new FormData();
    backendForm.append("user_photo", userPhoto);
    backendForm.append("cloth_url", clothUrl);

    const response = await fetch(`${API_URL}photo/try-on`, {
      method: "POST",
      headers: {
        "PK-apiToken": API_TOKEN,
        "PK-role": "User",
        "PK-country": "IN",
        "PK-timezone": "Asia/Kolkata",
      },
      body: backendForm,
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("❌ Try-on API error:", error);
    return NextResponse.json({ message: "Try-on failed" }, { status: 500 });
  }
}
