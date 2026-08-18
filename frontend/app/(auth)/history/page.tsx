"use client";

import { useState, useEffect, useRef } from "react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import { Calendar } from "lucide-react";
import { Loader } from "@/app/components/loader";

/* -------------------------------------------------------------------------- */
/*                                   TYPES                                    */
/* -------------------------------------------------------------------------- */

interface HistoryProduct {
  name: string;
  brand: string;
  price: string;
  imagePath: string | null;
}

interface HistoryEntry {
  id: number;
  date: string;
  imagePath: string | null;
  itemsFound: number;
  products: HistoryProduct[];
}

/* -------------------------------------------------------------------------- */
/*                               MAIN COMPONENT                               */
/* -------------------------------------------------------------------------- */

export default function HistoryFavoritesPage() {
  /* ------------------------------ STATE ------------------------------ */
  const [activeTab] = useState<"history" | "favorites">("history");
  const [historyData, setHistoryData] = useState<HistoryEntry[]>([]);
  const [loadingProducts, setLoadingProducts] = useState<boolean>(false);

  const [offset, setOffset] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(true);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const LIMIT = 10;

  /* --------------------------- INITIAL LOAD -------------------------- */
  useEffect(() => {
    fetchHistory(0);
  }, []);

  /* -------------------------- FETCH HISTORY --------------------------- */
  const fetchHistory = async (currentOffset: number) => {
    if (loadingProducts || !hasMore) return;

    try {
      setLoadingProducts(true);

      const res = await fetch("/api/history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          limit: LIMIT,
          offset: currentOffset,
        }),
      });

      const json = await res.json();
      const records = json?.data ?? [];

      const mappedHistory: HistoryEntry[] = records
        .map((record: any, index: number) => {
          const products: HistoryProduct[] = [];

          record.search_result?.forEach((result: any) => {
            result.items?.forEach((item: any) => {
              item.product_list?.forEach((product: any) => {
                products.push({
                  name: product?.name ?? "--",
                  brand: product?.brands?.[0] ?? "Unknown",
                  price: product?.price ? `₹ ${product.price}` : "--",
                  imagePath: product?.images?.[0]?.path
                    ? product.images[0].path
                        .replace(/\\/g, "/")
                        .replace(/ /g, "%20")
                    : null,
                });
              });
            });
          });

          return {
            id: record.id ?? currentOffset + index + 1,
            date: record.createdAt,
            imagePath: record.imagePath
              ? record.imagePath
                  .replace(/\\/g, "/")
                  .replace(/ /g, "%20")
              : null,
            itemsFound: products.length,
            products,
          };
        })
        .filter((entry: HistoryEntry) => entry.products.length > 0);

      // No more records available
      if (mappedHistory.length < LIMIT) {
        setHasMore(false);
      }

      // Append data (pagination)
      setHistoryData((prev) => {
      const existingIds = new Set(prev.map((item) => item.id));

      const filteredNew = mappedHistory.filter(
        (item) => !existingIds.has(item.id)
      );

      return [...prev, ...filteredNew];
    });

      setOffset((prev) => prev + LIMIT);
    } catch (error) {
      console.error("🔴 History fetch failed", error);
    } finally {
      setLoadingProducts(false);
    }
  };

  /* ------------------------ SCROLL HANDLER ---------------------------- */
  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el || loadingProducts || !hasMore) return;

    const isNearBottom =
      el.scrollTop + el.clientHeight >= el.scrollHeight - 150;

    if (isNearBottom) {
      fetchHistory(offset);
    }
  };

  /* -------------------------------------------------------------------------- */
  /*                                   RENDER                                   */
  /* -------------------------------------------------------------------------- */

  return (
    <DashboardLayout>
  <div className="w-full bg-[#252525B2] h-full p-4 sm:p-8 flex flex-col">
        {/* HEADER */}
        

 <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-300 tracking-tight">
          History
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Your search history and recognized products.
        </p>
      </div>
    </div>
    
        {/* CONTENT */}
        <div className="mt-6 w-full mx-auto overflow-hidden flex-1 pb-10">
          {activeTab === "history" && (
            <>
              {historyData.length === 0 ? (
                <Loader />
              ) : historyData.length === 0 ? (
                <p className="text-center text-gray-500">
                  No history found.
                </p>
              ) : (
                <div
                  ref={scrollRef}
                  onScroll={handleScroll}
                  className="space-y-5 h-full overflow-y-auto flex-1 scrollbar-hide"
                >
                  {historyData.map((entry) => (
                    <div
                      key={entry.id}
                      className="border border-gray-700 rounded-xl p-4 sm:p-5">
                      <div className="grid grid-cols-1 lg:grid-cols-[96px_1fr_auto] gap-4">
                        {/* PREVIEW IMAGE */}
                        <div className="w-full max-w-[96px] aspect-[3/4] rounded-lg overflow-hidden bg-gray-800">
                          {entry.imagePath ? (
                            <img
                              src={entry.imagePath}
                              alt="Search preview"
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                (e.currentTarget as HTMLImageElement).src =
                                  "https://via.placeholder.com/150";
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-xs text-gray-400">
                              No Image
                            </div>
                          )}
                        </div>

                        {/* DETAILS */}
                        <div className="flex flex-col items-start gap-2 text-sm text-gray-400">
                          <div className="flex items-center gap-1">
                            <Calendar size={15} />
                            <span>{entry.date}</span>
                          </div>

                          <div className="px-3 py-1 rounded-md text-white text-xs font-medium bg-[linear-gradient(90deg,#2B7FFF_0%,#1A4C99_100%)]">
                            {entry.itemsFound} Items Found
                          </div>

                          <p className="text-sm font-medium text-gray-300">
                            Recognized Items:
                          </p>

                          <div className="flex flex-col gap-5 max-h-[240px] overflow-y-auto sm:grid sm:grid-cols-2 sm:max-h-none lg:grid-cols-4">
                            {entry.products.map((p, i) => (
                              <div
                                key={i}
                                className="flex items-center gap-3 bg-gray-800 rounded-lg px-3 py-2"
                              >
                                <div className="w-10 h-10 bg-white rounded-md overflow-hidden">
                                  <img
                                    src={
                                      p.imagePath ??
                                      "/image-placeholder.png"
                                    }
                                    alt={p.name}
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                      e.currentTarget.src =
                                        "/image-placeholder.png";
                                    }}
                                  />
                                </div>

                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-semibold truncate">
                                    {p.name}
                                  </p>
                                  <p className="text-xs text-gray-500 truncate">
                                    {p.brand}
                                  </p>
                                </div>

                                <p className="text-sm font-semibold whitespace-nowrap">
                                  {p.price}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Pagination Loader */}
                  {loadingProducts && (
                    <div className="flex justify-center py-4">
                      <Loader />
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
