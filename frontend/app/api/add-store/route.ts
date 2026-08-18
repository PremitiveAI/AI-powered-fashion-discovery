import { NextResponse } from "next/server";
import axios from "axios";
import { API_URL, API_TOKEN } from "@/app/utils/api";

export async function POST(request: Request) {
  try {

    const body = await request.json();

    const config = {
      method: "post",
      maxBodyLength: Infinity,
      url: `${API_URL}store/save`,
      headers: {
        "Content-Type": "application/json",
        'PK-apiToken': API_TOKEN,
      },
      data: body,
      credentials: "include",
    };

    const response = await axios.request(config);
    console.log("🔵 RAW BACKEND RESPONSE:", response.data);

  // Error from backend structure
    if (response?.data?.Error?.message) {
      return NextResponse.json(
        { message: response.data.Error.message },
        { status: 400 }
      );
    }
  

     const res = NextResponse.json(
      { message: "Store created successfully" },
      { status: 200 }
    );


    return res;

  } catch (error: any) {
    console.log("🔴 Update User API ERROR DETAILS");
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
          "Something went wrong",
      },
      { status: error?.response?.status || 500 }
    );
  }
}
