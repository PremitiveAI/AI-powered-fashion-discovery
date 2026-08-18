import { NextResponse } from "next/server";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function GET(
  req: Request,
  context: { params: Promise<{ id: string }> }
) {
  try {
    // ✅ FIX: await params
    const { id } = await context.params;

    if (!id) {
      return NextResponse.json(
        { message: "Employee key missing" },
        { status: 400 }
      );
    }

    console.log("🔑 id ID:", id);

    const res = await fetch(
      `${API_URL}store/details/${id}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "PK-apiToken": API_TOKEN,
          "PK-role": "User",
          "PK-country": "IN",
          "PK-timezone": "Asia/Kolkata",
        },
      }
    );

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(
        { message: "Backend error", details: data },
        { status: res.status }
      );
    }

    return NextResponse.json(data);

  } catch (error: any) {
    console.error("🔴 EMPLOYEE DETAILS API ERROR:", error?.message);

    return NextResponse.json(
      {
        message: error?.message || "Internal server error",
      },
      { status: 500 }
    );
  }
}
