"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import { UploadCloud, ArrowLeft } from "lucide-react";
import SafeImage from "@/app/components/SafeImage";
import { Loader } from "@/app/components/loader";

/* ================= TYPES ================= */

interface DetectedProduct {
  product_id: string;
  product_title: string;
  brand: { name: string };
  price: number;
  confidence: number;
  images: { url: string; is_primary: boolean }[];
}

/* ================= COMPONENT ================= */

export default function UploadTryOnPage() {
  const router = useRouter();
  const [image, setImage] = useState<string | null>(null);
  const [products, setProducts] = useState<DetectedProduct[]>([]);
  const [tryOnLoading, setTryOnLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);


  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ================= LOAD PASSED LIST (OPTIONAL) ================= */

  useEffect(() => {
    const stored = sessionStorage.getItem("recognizedProducts");
    if (stored) {
      setProducts(JSON.parse(stored));
    }
  }, []);

  /* ================= HANDLERS ================= */

 const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;

  setUploadedFile(file);
  setImage(URL.createObjectURL(file)); // preview
};

const handleTryOn = async (clothUrl: string) => {
  if (!uploadedFile) {
    alert("Please upload your photo first");
    return;
  }

  try {
    setTryOnLoading(true);

    const formData = new FormData();
    formData.append("user_photo", uploadedFile); // actual file
    formData.append("cloth_url", clothUrl);      // product image url

    const res = await fetch("/api/try-on", {
      method: "POST",
      body: formData, // ✅ do NOT set Content-Type, fetch will set it automatically
    });

    const data = await res.json();

    if (data?.image_url) {
      setImage(data.image_url); // replace uploaded image
    }
  } catch (err) {
    console.error("Try-on failed", err);
    alert("Try on failed. Please try again.");
  } finally {
    setTryOnLoading(false);
  }
};

  /* ================= UI ================= */

  return (
    <DashboardLayout>
      <div className="w-full  rounded-3xl p-6">

 {/* Loader */}
    {tryOnLoading && (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
        <Loader size="lg" />
      </div>
    )}

<button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-xl sm:text-xl lg:text-2xl
            font-bold text-gray-300 px-2">
            <ArrowLeft className="w-6 h-6 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
            <span>Upload Clothes To Try On</span>
          </button>

        {/* <h1 className="text-3xl font-bold mb-6">Upload Clothes To Try On</h1> */}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* ================= UPLOAD IMAGE ================= */}
          <div className="lg:col-span-4 flex flex-col mx-4 xl:mx-10 gap-6 mt-8">
            <div className="bg-gray-900 rounded-4xl px-4 lg:px-6 xl:px-10 pt-6 lg:pt-8 pb-4 shadow-md flex flex-col gap-4">
              <label
                htmlFor="upload"
                className={`aspect-[6/7] rounded-4xl flex flex-col items-center justify-center overflow-visible text-center cursor-pointer transition-all duration-300
                  ${image ? "border-none" : "border-2 border-dashed border-purple-300 hover:bg-gray-800"}
                `}
              >
                {image ? (
                  <img
                    src={image}
                    alt="Uploaded"
                    className="max-h-full max-w-full object-cover rounded-xl"
                  />
                ) : (
                  <div className="text-center">
                    <UploadCloud className="mx-auto mb-2 text-purple-500" />
                    <p className="text-sm font-medium text-gray-700">
                      Click or drag image to upload
                    </p>
                  </div>
                )}
              </label>

              <input
                ref={fileInputRef}
                id="upload"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileSelect}
              />

              <button
              onClick={() => fileInputRef.current?.click()}
                
                className="py-3 rounded-xl font-semibold bg-gradient-to-r from-purple-500 to-purple-700 text-white disabled:opacity-50"
              >
                {uploadedFile ? "Upload Your Another Photo" : "Upload Your Photo"}
                
              </button>
            </div>
          </div>

          {/* ================= RECOGNIZED LIST ================= */}
          <div className="lg:col-span-8">

            <div
                className="
                  flex flex-nowrap gap-6
                  overflow-x-auto scrollbar-hide
                  snap-x snap-mandatory
                  px-4 py-8
                "
              >
                {products.map((product) => {
                  const primaryImage =
                    product.images.find((img) => img.is_primary)?.url ||
                    product.images[0]?.url;

                  return (
                    <div
                      key={product.product_id}
                      className="
                        min-w-[240px] max-w-[240px]
                        bg-gray-900 rounded-2xl p-4
                        shadow-lg cursor-pointer
                        hover:ring-2 hover:ring-gray-500
                        transition
                      "
                    >
                      <div className="aspect-square bg-gray-100 rounded-xl mb-2 overflow-hidden">
                        <SafeImage
                          src={primaryImage}
                          alt={product.product_title}
                        />
                      </div>

                      <p className="text-sm font-medium truncate">
                        {product.product_title}
                      </p>

                      <p className="text-xs text-gray-500">
                        {product.brand?.name}
                      </p>

                      <div className="flex justify-between items-center mt-1 text-sm">
                        <span className="font-semibold">
                          ₹ {product.price}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                          {Math.round(product.confidence * 100)}%
                        </span>
                      </div>
                      <button
                        className="w-full mt-3 py-2 bg-[#EBF4FF] text-[#0056B3] font-bold text-sm rounded-lg border border-[#D1E9FF] hover:bg-[#DBEAFE] transition-colors disabled:opacity-60"
                        disabled={tryOnLoading}
                        onClick={(e) => {
                          e.stopPropagation();

                          const clothImage =
                            product.images.find((img) => img.is_primary)?.url ||
                            product.images[0]?.url;

                          handleTryOn(clothImage);
                        }}
                      >
                        Try On
                      </button>

                    </div>
                  );
                })}
              </div>

          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
