"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { ArrowRight } from "lucide-react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import GeneratingLook from "@/app/(auth)/phase2/loading/GeneratingLook";
import Toast from "@/app/components/toast";
import { Loader } from "@/app/components/loader";

interface ProductListItem {
  id: number;
  hsn_code: string;
  product_code: string;
  name: string;
  mrp: number;
  price: number;
  gender: string;
  category: {
    id: number;
    name: string;
  };
  subtype: {
    id: number;
    name: string;
  };
  pattern: {
    id: number;
    name: string;
  };
  brands: string[];
  colors: string[];
  images: {
    id: number;
    path: string;
  }[];
  product_intro: string;
  description: string;
  specification: string;
  createdAt: string;
  updatedAt: string;
  status: number;
  score: number;
}

interface LookItem {
  id: number;
  category: string;
  type: string;
  subtype: string | null;
  color: string;
  pattern: string;
  brand: string | null;
  gender: string;
  status: boolean;
  shade: string | null;
  product_list: ProductListItem[]; // or a specific ProductItem[] if you have that type
}

interface LookModel {
  id: number;
  cosmetics_name: string;
  cosmetics_url: string;
  user_url: string | null;
  prompt: string;
  gender: string;
  status: boolean;
  items: LookItem[];
}

interface LookCategory {
  id: number;
  name: string;
  type: string;
  description: string;
}

interface LookGroup {
  category: LookCategory;
  models: LookModel[];
}

interface LooksResponse {
  status: string;
  data: LookGroup[];
}

export default function FashionDashboard() {

  const router = useRouter();
  const [showGenerating, setShowGenerating] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastType, setToastType] = useState<"success" | "error">("success");
  const [loading, setLoading] = useState(false);

  const [modelList, setModelList] = useState<LookGroup[]>([]);
  
  const [tryOnResults, setTryOnResults] = useState<Record<number, string>>({});
  const [tryOnLoading, setTryOnLoading] = useState<Record<number, boolean>>({});

  const searchParams = useSearchParams();

  const [profileId, setProfileId] = useState(Number);

  const [selectedCategoryIds, setSelectedCategoryIds] = useState<number[]>([]);

  const hasFetchedRecommendations = useRef(false);
  const hasFetchedProfile = useRef(false);
  const hasFetchedCategory = useRef(false);

  /* ===== Toast ===== */
  const showToast = (msg: string, type: "success" | "error") => {
    setToastMessage(msg);
    setToastType(type);
    setTimeout(() => setToastMessage(null), 3000);
  };

  useEffect(() => {
    if (hasFetchedProfile.current) return;
    hasFetchedProfile.current = true;

  const getProfileID = async () => {
    try {
      setLoading(true);

        const res = await fetch("/api/phase3/get-user-photo");
        const data = await res.json();

        if (data?.id) {
          setProfileId(data.id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    getProfileID();
  }, []);

  useEffect(() => {
    if (hasFetchedCategory.current) return;
    hasFetchedCategory.current = true;

    const fetchGetCategory = async () => {
      try {
        setLoading(true);

        const res = await fetch("/api/phase3/get-categories", {
        method: "GET",
      });

      if (!res.ok) {
        throw new Error("Failed to fetch user photo");
      }

        const result = await res.json();
        console.log("API Response:", result);

        if (result?.data) {
          setSelectedCategoryIds(
            Array.isArray(result.data.category_ids)
              ? result.data.category_ids
              : []
          );
      }
    } catch (err) {
      console.error("Try-on failed", err);
      alert("Try on failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

    fetchGetCategory();
  }, []);


  useEffect(() => {
    if (!selectedCategoryIds.length) return;

    const fetchRecommendations = async () => {
      try {
        setLoading(true);

        const res = await fetch("/api/phase3/cosmetic-list", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(selectedCategoryIds),
        });

        const json = await res.json();

        if (json.status === "success") {
        setModelList(json.data);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [selectedCategoryIds]);

  const handleTryOn = async (cosmeticsId: number) => {
    try {
      setShowGenerating(true);

      const res = await fetch("/api/phase3/user-try-on", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: profileId, model_id: cosmeticsId }),
    });

    if (!res.ok) throw new Error("Failed to fetch user photo");
    const data = await res.json();

      if (data?.image_url) {
      setTryOnResults((prev) => ({ ...prev, [cosmeticsId]: data.image_url }));
    }
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    } finally {
      setTryOnLoading((prev) => ({ ...prev, [cosmeticsId]: false }));
      setShowGenerating(false);
    }
  };

  const handleLookDetail = (cosmeticsId: number) => {
    setSelectedModelId(cosmeticsId);
    router.push(`/phase3/look-detail?cosmeticsId=${cosmeticsId}&profileId=${profileId}`);
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen h-auto overflow-y-auto bg-[#0A0A0A] text-white font-sans selection:bg-purple-500/30">

        {toastMessage && toastType && (
          <Toast message={toastMessage} type={toastType} />
        )}

        {loading && (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
            <Loader size="lg" />
          </div>
        )}
      
        {showGenerating && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/40 backdrop-blur-md" />
            <div className="relative z-10 w-full h-full">
              <GeneratingLook id={null} />
            </div>
          </div>
        )}

        {/* --- SCROLLABLE CONTAINER --- */}
        <div className="max-w-7xl mx-auto px-6 py-10 space-y-16 overflow-x-hidden">

          {modelList.map((group, groupIndex) => {
            const isPosition1 = groupIndex === 0;   // Layout 1
            const isPosition2 = groupIndex === 1;  // Layout 2
            const isPosition3 = groupIndex === 2;  // Layout 3
            const isLast = groupIndex >= 3;        // Layout 6

            return (
              <div key={group.category.id}>
                <section className="space-y-6">

                  {/* Header */}
                  <div className="flex justify-between items-end">
                    <div>
                      <h2 className="text-4xl font-serif font-light tracking-tight italic">
                        {group.category.name}
                      </h2>
                      <p className="text-gray-400 text-sm uppercase tracking-[0.2em] mt-1">
                        {group.category.description}
                      </p>
                    </div>
                    <button className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm uppercase tracking-[0.2em]"> Explore All <ArrowRight className="w-4 h-4" /> </button>
                  </div>

                  {isLast ? (
                    <section className="bg-[#121212] rounded-[3rem] p-10 space-y-12">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-1 px-2">
                        {group.models.map((model) => {
                          const displayImage = tryOnResults[model.id] || model.user_url || model.cosmetics_url;
                          return (
                            <div key={model.id} className="group relative bg-[#1A1A1A] overflow-hidden">

                              <div className="aspect-[4/5] overflow-hidden">
                                <img
                                  src={displayImage}
                                  alt={model.cosmetics_name}
                                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 cursor-grab active:cursor-grabbing"
                                  onClick={() => handleLookDetail(model.id)}
                                />
                              </div>

                              <div className="absolute bottom-0 left-0 w-full bg-black/60 backdrop-blur-md p-4 flex items-center justify-between">
                                {model.items.slice(0, 2).map((item) => (
                                  <div key={item.id} className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-full bg-gray-500 overflow-hidden">
                                      <img
                                        src={item.product_list?.[0]?.images?.[0]?.path ?? model.cosmetics_url}
                                        alt={item.type}
                                        className="w-full h-full object-cover"
                                      />
                                    </div>
                                    <div className="text-white text-xl font-semibold">
                                     ₹ {item.product_list?.[0]?.price ?? 1199}
                                    </div>
                                  </div>
                                ))}
                                <button
                                  onClick={(e) => {
                                  e.stopPropagation();   // ⬅️ Prevent parent click
                                  handleTryOn(model.id);
                                }}
                                  className="py-3 px-4 rounded-xl text-white text-xs font-semibold uppercase tracking-[0.15em]"
                                  style={{
                                    background: "rgba(255,255,255,0.12)",
                                    border: "1px solid rgba(255,255,255,0.22)",
                                    backdropFilter: "blur(10px)",
                                  }}
                                >
                                  ✨ Try On
                                </button>

                              </div>

                            </div>
                          )
                        })}
                      </div>
                    </section>
                  ) : isPosition1 ? (
                    <div className="flex gap-6 overflow-x-auto pb-4 snap-x snap-mandatory">
                      {group.models.map((model) => {
                        const displayImage = tryOnResults[model.id] || model.user_url || model.cosmetics_url;
                        return (
                          <div
                            key={model.id}
                            className="min-w-[300px] md:min-w-[480px] aspect-[4/5] relative rounded-[2rem] overflow-hidden snap-start group cursor-grab active:cursor-grabbing"
                            onClick={() => handleLookDetail(model.id)}
                          >
                            <img
                              src={displayImage}
                              alt={model.cosmetics_name}
                              className="absolute inset-0 w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                            />

                            {/* Right Glass Panel */}
                            <div
                              className="absolute right-0 top-0 h-full w-[30%] flex flex-col justify-between px-3 py-5"
                              style={{
                                background: "linear-gradient(180deg, rgba(245, 98, 19, 0.4) 0%, rgba(53, 14, 4, 0.5) 100%)",
                                backdropFilter: "blur(3px)",
                                borderLeft: "0px solid rgba(255,255,255,0.08)",
                              }}
                            >
                              <div className="flex flex-col gap-4 flex-1 justify-center">
                                {model.items.slice(0, 3).map((item) => (
                                  <div key={item.id} className="flex flex-col items-center gap-1">
                                    <div className="w-18 h-18 rounded-full overflow-hidden">
                                      <img
                                        src={item.product_list?.[0]?.images?.[0]?.path ?? model.cosmetics_url}
                                        alt={item.type}
                                        className="w-full h-full object-cover"
                                      />
                                    </div>
                                    <div className="text-white text-xl font-semibold">
                                     ₹ {item.product_list?.[0]?.price ?? 1349}
                                    </div>
                                  </div>
                                ))}
                              </div>

                              <button
                                onClick={(e) => {
                                  e.stopPropagation();   // ⬅️ Prevent parent click
                                  handleTryOn(model.id);
                                }}
                                className="py-3 px-4 rounded-xl text-white text-xs font-semibold uppercase tracking-[0.15em]"
                                style={{
                                  background: "rgba(255,255,255,0.12)",
                                  border: "1px solid rgba(255,255,255,0.22)",
                                  backdropFilter: "blur(10px)",
                                }}
                              >
                                ✨ Try On
                              </button>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  ) : isPosition2 ? (
                    <div className="flex gap-6 overflow-x-auto pb-4 snap-x snap-mandatory">
                      {group.models.map((model) => {
                        const displayImage = tryOnResults[model.id] || model.user_url || model.cosmetics_url;
                        return (
                          <div
                            key={model.id}
                            className="min-w-[300px] md:min-w-[480px] aspect-[4/5] relative rounded-[2rem] overflow-hidden snap-start group cursor-grab active:cursor-grabbing"
                            onClick={() => handleLookDetail(model.id)}
                          >
                            <img
                              src={displayImage}
                              alt={model.cosmetics_name}
                              className="absolute inset-0 w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                            />

                            {/* Bottom Glass Panel */}
                            <div
                              className="absolute bottom-0 left-0 w-full flex flex-col items-center gap-3 px-4 pt-6 pb-5"
                              style={{
                                background: "linear-gradient(180deg, rgba(245, 98, 19, 0.4) 0%, rgba(53, 14, 4, 0.5) 100%)",
                                backdropFilter: "blur(22px)",
                                borderTop: "1px solid rgba(255,255,255,0.08)",
                              }}
                            >
                              <div className="flex flex-row gap-6 justify-center items-center w-full overflow-x-auto scrollbar-hide ">
                                {model.items.slice(0, 3).map((item) => (
                                  <div key={item.id} className="flex flex-col items-center gap-1">
                                    <div className="w-18 h-18 rounded-xl overflow-hidden">
                                      <img
                                        src={item.product_list?.[0]?.images?.[0]?.path ?? model.cosmetics_url}
                                        alt={item.type}
                                        className="w-full h-full object-cover"
                                      />
                                    </div>
                                    <div className="text-white text-xl font-semibold">
                                     ₹ {item.product_list?.[0]?.price ?? 1299}
                                    </div>
                                  </div>
                                ))}
                              </div>

                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTryOn(model.id);
                                }}
                                className="w-full max-w-[180px] py-3 px-4 rounded-xl text-white text-xs font-semibold uppercase tracking-[0.15em]"
                                style={{
                                  background: "rgba(255,255,255,0.12)",
                                  border: "1px solid rgba(255,255,255,0.22)",
                                  backdropFilter: "blur(10px)",
                                }}
                              >
                                ✨ Try On
                              </button>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  ) : isPosition3 ? (
                    <div className="flex gap-6 overflow-x-auto pb-4 snap-x snap-mandatory">
                      {group.models.map((model) => {
                        const displayImage = tryOnResults[model.id] || model.user_url || model.cosmetics_url;
                        return (
                          <div
                            key={model.id}
                            className="min-w-[300px] md:min-w-[480px] aspect-[4/5] relative rounded-[2rem] overflow-hidden snap-start group cursor-grab active:cursor-grabbing"
                            onClick={() => handleLookDetail(model.id)}
                          >
                            <img
                              src={displayImage}
                              alt={model.cosmetics_name}
                              className="absolute inset-0 w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                            />

                            <div
                              className="absolute bottom-0 left-0 w-full flex flex-col items-center gap-3 px-4 pt-6 pb-5 bg-black/60 backdrop-blur-md ">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();   // ⬅️ Prevent parent click
                                  handleTryOn(model.id);
                                }}
                                className="w-full max-w-[180px] py-3 px-4 rounded-xl text-white text-xs font-semibold uppercase tracking-[0.15em]"
                                style={{
                                  background: "rgba(255,255,255,0.12)",
                                  border: "1px solid rgba(255,255,255,0.22)",
                                  backdropFilter: "blur(10px)",
                                }}
                              >
                                ✨ Try On
                              </button>
                            </div>

                            {/* Bottom Glass Panel */}
                            {/* <div
                              className="absolute bottom-0 left-0 w-full flex flex-col items-center gap-3 px-4 pt-6 pb-5"
                              style={{
                                background:"linear-gradient(180deg, rgba(245, 98, 19, 0.4) 0%, rgba(53, 14, 4, 0.5) 100%)",
                                backdropFilter: "blur(22px)",
                                borderTop: "1px solid rgba(255,255,255,0.08)",
                              }}
                            >
                              <div className="flex flex-row gap-6 justify-center items-center w-full overflow-x-auto">
                                {model.items.map((item) => (
                                  <div key={item.id} className="flex flex-col items-center gap-1">
                                    <div className="w-18 h-18 rounded-xl overflow-hidden">
                                      <img
                                        src={item.product_list?.[0]?.image_url ?? model.cosmetics_url}
                                        alt={item.type}
                                        className="w-full h-full object-cover"
                                      />
                                    </div>
                                    <span className="text-white text-[10px] capitalize">
                                      {item.color} {item.type}
                                    </span>
                                  </div>
                                ))}
                              </div>

                              <button
                                onClick={(e) => {
                                  e.stopPropagation();   // ⬅️ Prevent parent click
                                  handleTryOn(model.id);
                                }}
                                className="w-full max-w-[180px] py-3 px-4 rounded-xl text-white text-xs font-semibold uppercase tracking-[0.15em]"
                                style={{
                                  background: "rgba(255,255,255,0.12)",
                                  border: "1px solid rgba(255,255,255,0.22)",
                                  backdropFilter: "blur(10px)",
                                }}
                              >
                                ✨ Try On
                              </button>
                            </div> */}
                          </div>
                        )
                      })}
                    </div>
                  ) : null}
                </section>
                {groupIndex < modelList.length - 1 && (<div className="max-w-4xl mx-auto h-[1px] bg-white/5 my-16 shadow-[0_1px_2px_rgba(255,255,255,0.05)]" />)}
              </div>
            );
          })}
        </div>

        {/* CUSTOM SCROLLBAR HIDE */}
        <style jsx global>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
      </div>

      {showGenerating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-md"
            onClick={() => setShowGenerating(false)}
          />
          <div className="relative z-10 w-full h-full">
            <GeneratingLook id={selectedModelId} />  {/* 👈 pass it here */}
          </div>
        </div>
      )}

    </DashboardLayout>
  );
}