import { NextResponse } from "next/server";
import axios from "axios";
import { cookies } from "next/headers";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function POST(req: Request) {
  try {
    const cookieStore = cookies();

    // ✅ Read request body from frontend
    const body = await req.json();

    const {
      search = "",
      filter = { category_id: 0 },
      startDate = "",
      endDate = "",
      sort = "createdAt",
      order = "DESC",
      limit = 10,
      offset = 0,
    } = body;

    // ✅ Payload exactly as backend expects
    const payload = {
      search,
      filter:
    typeof filter === "object" && filter !== null
      ? filter
      : { category_id: 0 },
      startDate,
      endDate,
      sort,
      order,
      limit,
      offset,
    };

    const { data } = await axios.post(
      `${API_URL.replace(/\/$/, "")}/product/historylist`,
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

    console.log("🟢 PRODUCT HISTORY API – BACKEND PAYLOAD:", payload);

    // ❌ Backend error handling
    if (data?.Error) {
      return NextResponse.json(
        { message: data.Error?.message || "Backend error" },
        { status: 400 }
      );
    }

    // ✅ Normalize response for frontend
    // ✅ Normalize response for frontend (FIXED)
const records = data?.Success?.data?.records ?? [];
const totalRecords = data?.Success?.data?.total ?? 0;

return NextResponse.json(
  {
    message: "Product history fetched successfully",
    totalRecords,
    data: records,
  },
  { status: 200 }
);

  } catch (error: any) {
    console.error("🔴 PRODUCT HISTORY API ERROR");
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
