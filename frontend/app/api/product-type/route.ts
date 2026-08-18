import { NextResponse } from "next/server";
import { API_URL, API_TOKEN } from "@/app/utils/api";
import axios from "axios";

// ✅ only change: GET -> POST (and accept Request if you want later)
export async function POST() {
  try {

    const payload = {
      search: "",
      filter: "",
      startDate: "",
      endDate: "",
      sort: "createdAt",
      order: "DESC",
      limit: 10,
      offset: 0,
    };

    const { data } = await axios.post(
      `${API_URL}master/product/list`,
      payload,
      {
        headers: {
          "Content-Type": "application/json",
          "PK-apiToken": API_TOKEN,
        },
      }
    );
  console.log("🔵 RAW BACKEND RESPONSE:", data);

 // Error from backend structure
    if (data?.Error?.message) {
      return NextResponse.json(
        { message:data.Error.message },
        { status: 400 }
      );
    }
  

     const res = NextResponse.json(
      { message: "API call successful" },
      { status: 200 }
    );

    const list = data?.Success?.data?.list ?? [];
    return NextResponse.json({ data: list }, { status: 200 });

  } catch (error: any) {
    console.log("🔴 Feature master API ERROR DETAILS");
    console.log("error.message:", error?.message);
    console.log("error.response?.status:", error?.response?.status);
    console.log("error.response?.data:", error?.response?.data);
    console.log("error.config?.url:", error?.config?.url);

    return NextResponse.json(
      {
        message:
          error?.response?.data?.Error?.message ||
          error?.response?.data?.detail ||
          error?.message ||
          "File upload failed or server error",
      },
      { status: error?.response?.status || 500 }
    );
  }
}
