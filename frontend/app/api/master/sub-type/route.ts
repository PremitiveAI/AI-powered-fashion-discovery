import { NextResponse } from "next/server";
import axios from "axios";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const response = await axios.post(
      `${API_URL}master/subtype/list`,
      body,
      {
        headers: {
          "Content-Type": "application/json",
          "PK-apiToken": API_TOKEN,
          "PK-role": "User",
          "PK-country": "IN",
          "PK-timezone": "Asia/Kolkata",
        },
      }
    );

    return NextResponse.json(response.data, { status: 200 });
  } catch (error: any) {
    console.error("❌ Category API error:", error?.response?.data || error);

    return NextResponse.json(
      {
        message:
          error?.response?.data?.Error?.message ||
          error?.message ||
          "Something went wrong",
      },
      { status: error?.response?.status || 500 }
    );
  }
}
