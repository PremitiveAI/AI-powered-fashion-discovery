import { NextResponse } from "next/server";
import axios from "axios";
import { cookies } from "next/headers";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function POST(req: Request) {
  try {
    const cookieStore = cookies();
    // ✅ Payload exactly as backend expects
     const body = await req.json();

    const {
      products_id = [],
      latitude = 0,
      longitude = 0,
       store_type = "",
    } = body;

    const payload = {
      search: "",
      store_type,
      products_id,
      latitude,
      longitude,
      sort: "createdAt",
      order: "DESC",
      limit: 100,
      offset: 0,
    };

    const { data } = await axios.post(
      `${API_URL.replace(/\/$/, "")}/store/list`,
      payload,
      {
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
          "PK-apiToken": API_TOKEN,
          "PK-role": "User",
          "PK-country": "IN",
          "PK-timezone": "Asia/Kolkata",
        },
      }
    );

    console.log("🟢 STORE LIST API – BACKEND PAYLOAD:", payload);
    // ❌ Backend error handling
    if (data?.Error) {
      return NextResponse.json(
        { message: data.Error?.message || "Backend error" },
        { status: 400 }
      );
    }

    // ✅ Normalize response for frontend
    const list = data?.Success?.data?.list ?? [];
    const totalRecords = data?.Success?.data?.totalRecords ?? 0;

    return NextResponse.json(
      {
        message: "Store list fetched successfully",
        totalRecords,
        data: list,
      },
      { status: 200 }
    );
  } catch (error: any) {
  console.error("🔴 STORE LIST API ERROR");
    console.error("message:", error?.message);
    console.error("status:", error?.response?.status);
    console.error("data:", error?.response?.data);
    console.error("url:", error?.config?.url);

    return NextResponse.json(
      {
        message:
          error?.response?.data?.Error?.message ||
          error?.response?.data?.detail ||
          error?.message ||
          "Server error",
      },
      { status: error?.response?.status || 500 }
    );
  }
}
