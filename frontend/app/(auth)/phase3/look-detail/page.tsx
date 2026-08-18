"use client";

import Image from "next/image";
import { useState, useRef, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import GeneratingLook from "@/app/(auth)/phase2/loading/GeneratingLook";
import Toast from "@/app/components/toast";
import { Loader } from "@/app/components/loader";

export default function LookDetailPage() {

  const router = useRouter();
  const [showGenerating, setShowGenerating] = useState(false);

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastType, setToastType] = useState<"success" | "error">("success");
  const [imageLoading, setImageLoading] = useState(false);
  const [loading, setLoading] = useState(false);

  const [tryOn, setTryOn] = useState<string | null>(null);
  const searchParams = useSearchParams();

  const cosmeticsId = searchParams.get("cosmeticsId");
  const profileId = searchParams.get("profileId");
  const [lookData, setLookData] = useState<any>(null);

  const hasFetched = useRef(false);

  const displayImage = tryOn || lookData?.user_url  || lookData?.cosmetics_url;
  const isModelImage = !tryOn && !lookData?.user_url && !!lookData?.cosmetics_url;

  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  useEffect(() => {
    console.log("profileId:", profileId);
    console.log("cosmeticsId:", cosmeticsId);
  }, [profileId, cosmeticsId]);

  /* ===== Toast ===== */
  const showToast = (msg: string, type: "success" | "error") => {
    setToastMessage(msg);
    setToastType(type);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const fetchTryOn = async () => {
    try {
      setImageLoading(true);

      const payload = {
        user_id: profileId,
        cosmetics_id: Number(cosmeticsId),
      };

      const res = await fetch("/api/phase3/user-try-on", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error("Failed to fetch user photo");
      }

      const data = await res.json();

      if (data?.image_url) {
        setTryOn(data.image_url);
        showToast("Look generated successfully ✨", "success");
      }
    } catch (error) {
      console.error("Failed to fetch categories:", error);
      showToast("Failed to generate look", "error");
    } finally {
      setImageLoading(false);
    }
  };

   const fetchLookDetails = async () => {
      try {
        setLoading(true);

        const payload = {
          cosmetics_id: cosmeticsId,
        };

        const res = await fetch("/api/phase3/cosmetic-detail", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error("Failed to fetch look details");

      const json = await res.json();
      console.log("API Response:", json);

      setLookData(json.data);
        
      } catch (error) {
        console.error("Failed to fetch categories:", error);
      } finally {
        setLoading(false);
      }
    };

  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    fetchLookDetails();
  }, []);

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-[#0d0f14] text-white px-10 py-12">

        {toastMessage && toastType && (
          <Toast message={toastMessage} type={toastType} />
        )}

        {imageLoading && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/40 backdrop-blur-md" />
            <div className="relative z-10 w-full h-full">
              <GeneratingLook id={null} />
            </div>
          </div>
        )}

        {loading && (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
            <Loader size="lg" />
          </div>
        )}
        
        <button
          onClick={() => router.back()}
          className="flex items-center gap-3 font-semibold 
             text-3xl text-gray-600 
             hover:text-white 
             transition-colors duration-200 mb-6"
        >
          <ChevronLeft className="w-7 h-7" />
          Back
        </button>

        {/* TOP SECTION */}
        <div className="grid grid-cols-[1fr_1.3fr] gap-16">
          {!loading && (
            <div className="relative ml-20 mr-20 aspect-[4/5] max-h-[750px] rounded-3xl p-[2px] bg-gradient-to-br from-purple-500 via-fuchsia-500 to-indigo-500">
              <div className="relative w-full h-full rounded-3xl overflow-hidden group cursor-grab active:cursor-grabbing">

                {/* Image */}
                {displayImage && (
                  <>
                    <img
                      src={displayImage}
                      alt="Look"
                      onClick={() => setIsPreviewOpen(true)}
                      className="absolute inset-0 w-full h-full object-cover object-center"
                    />

                    {/* Optional overlay for better contrast */}
                    <div className="absolute inset-0 bg-black/20 pointer-events-none" />
                  </>
                )}

              {/* TRY ON BUTTON */}
              {!lookData?.user_url && !tryOn && (
                <button
                  onClick={fetchTryOn}
                  className="absolute bottom-6 left-1/2 -translate-x-1/2
                   px-6 py-3 rounded-xl
                   bg-white/20 backdrop-blur-md
                   border border-white/30
                   text-white text-sm tracking-widest uppercase
                   hover:bg-white/30 transition"
                   
                >
                  ✨ Try On
                </button>
              )}

            </div>
          </div>
        )}

          {/* RIGHT CONTENT */}
          {lookData && (
            <div>
              <p className="text-xs tracking-widest text-gray-500 uppercase mb-3">
                Personalized Edit • Look #{String(lookData.id).padStart(3, "0")}
              </p>

              <h1 className="text-5xl font-serif mb-6">
                {lookData.category?.name} — {lookData.category?.description}
              </h1>

              <p className="text-gray-400 text-2xl leading-relaxed mb-8">
                {lookData.prompt}
              </p>

              {/* OUTFIT BREAKDOWN */}
              <div>
                <div className="flex justify-between text-m text-gray-500 uppercase tracking-widest mb-6">
                  <span>Outfit Breakdown</span>
                  <span>{lookData.items?.length ?? 0} Items</span>
                </div>

                {lookData.items.map((item: any) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between py-4 border-b border-white/5"
                  >
                    <div className="flex items-center gap-4">
                      {/* Placeholder image since product_list is empty */}
                      <div className="w-18 h-18 rounded-full bg-gray-500 overflow-hidden">                        <img
                          src={item.product_list?.[0]?.images?.[0]?.path ?? lookData.cosmetics_url}
                          alt={item.type}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="text-white text-xl font-semibold">
                                     ₹ {item.product_list?.[0]?.price ?? 1199}
                                    </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="max-w-7xl mx-auto h-[1px] bg-white/5 my-16 shadow-[0_1px_2px_rgba(255,255,255,0.05)]" />

        {/* SIMILAR OUTFITS */}
        {lookData?.similar_models?.length > 0 && (
          <div>
            <h2 className="text-4xl font-serif mb-10">Similar Outfits</h2>

            <div className="grid grid-cols-3 gap-10">
              {lookData.similar_models.map((model: any) => (
                <div
                  key={model.id}
                  className="rounded-3xl overflow-hidden bg-[#111318] hover:scale-[1.02] transition duration-500"
                >
                  <div className="aspect-[8/9] overflow-hidden">
                  <img
                    src={model.user_url || model.cosmetics_url}
                    alt={model.cosmetics_name}
                    className="w-full h-full object-contain transition-transform duration-700"
                  />
                  </div>

                  <div className="bg-white/10 backdrop-blur-md p-4">
                    <p className="text-xl text-gray-300">
                      {model.category?.name} — {model.category?.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {showGenerating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">

          {/* 🔥 Background Blur Layer */}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-md"
            onClick={() => setShowGenerating(false)}
          />

          {/* 🔥 Generating Screen */}
          <div className="relative z-10 w-full h-full">
            <GeneratingLook id={null} />
          </div>
        </div>
      )}

      {isPreviewOpen && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8">

          {/* Close Button */}
          <button
            onClick={() => setIsPreviewOpen(false)}
            className="absolute top-6 right-6 text-white text-3xl font-bold"
          >
            ✕
          </button>

          {/* Fullscreen Image */}
          <img
            src={displayImage}
            alt="Preview"
            className="w-full h-full object-contain"
          />
        </div>
      )}
    </DashboardLayout>
  );
}
