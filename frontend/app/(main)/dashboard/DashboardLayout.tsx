"use client";

import React, { useState, useEffect } from "react";

import { useRouter, usePathname } from "next/navigation";
import { Menu, HomeIcon, LayoutDashboard, Shirt, User, Bookmark, History, Search, Package, Store, Stars } from "lucide-react";
import { Button } from "@/app/components/button";
import { profile } from "console";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const capitalize = (name: string) =>
    name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();

  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [showLogoutPopup, setShowLogoutPopup] = useState(false);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);

  useEffect(() => {
    const cookieString = document.cookie;
    const match = cookieString.match(/(?:^|;\s*)username=([^;]+)/);

    if (match && match[1]) {
      setUsername(decodeURIComponent(match[1]));
    }
  }, []);

  const menuItems = [
    // ================= DASHBOARD =================
    {
      icon: LayoutDashboard,
      label: "Dashboard",
      path: "/dashboard",
    },
    // ================= HOME =================
    {
      icon: HomeIcon,
      label: "Home",
      path: "/phase2/home",
    },
    // ================= SEARCH =================
    {
      icon: Search,
      label: "Search",
      path: "/uploade",
    },
    // ================= STYLE =================
    {
      icon: Shirt,
      label: "Style Profile",
      path: "/phase2/style-profile"
    },
    // ================= VANITY =================
    {
      icon: Stars,
      label: "Vanity",
      path: "/phase3/home"
    },
    // ================= BEAUTY STYLE =================
    {
      icon: User,
      label: "Beauty Profile",
      path: "/phase3/beauty-profile"
    },
    // ================= PRODUCT =================
    {
      icon: Package,
      label: "Product",
      children: [
        {
          label: "Add Product",
          path: "/add-product",
        },
        {
          label: "Product List",
          path: "/product-list",
        },
      ],
    },
    // ================= STORE =================
    {
      icon: Store,
      label: "Store",
      children: [
        {
          label: "Add Store",
          path: "/add-store",
        },
        {
          label: "Store List",
          path: "/store-list",
        },
      ],
    },
  ];

  const collectionItems = [
    {
      icon: Bookmark,
      label: "Saved Looks",
      path: "",
    },
    {
      icon: History,
      label: "History",
      path: "/history",
    },
  ];

  // Auto-open menu if any child is active
  useEffect(() => {
    menuItems.forEach((item) => {
      if (item.children?.some((child) => pathname === child.path)) {
        setOpenMenu(item.label);
      }
    });
  }, [pathname]);

  return (
    <div className="relative z-10 flex justify-center items-center w-full h-screen block">
      <div className="w-full h-full bg-black border border-zinc-800 shadow-[0_0_60px_rgba(168,85,247,0.06)] overflow-hidden">
        <div className="flex h-full">
          {/* Sidebar */}
          <aside
            className={`
    absolute lg:relative left-0 top-0 h-full w-72
    z-50 flex flex-col
    transition-transform duration-300
    ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"}
    lg:translate-x-0
    bg-black
  `}
          >
            <div className="flex flex-col h-full px-6 pt-8 pb-6">

              {/* LOGO */}
              <div className="mb-10">
                <img
                  src="/logo.svg"
                  alt="Logo"
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="h-[1px] w-full bg-white/20 mb-6"></div>

              {/* MAIN NAVIGATION */}
              <nav className="flex flex-col gap-3">

                {menuItems.map((item, idx) => {
                  const Icon = item.icon;

                  const isActiveParent =
                    pathname === item.path ||
                    item.children?.some((child) => pathname === child.path);

                  const isOpen = openMenu === item.label;

                  return (
                    <div key={idx} className="w-full">

                      {/* Parent Button */}
                      <button
                        key={idx}
                        onClick={() => {
                          if (item.children) {
                            setOpenMenu(isOpen ? null : item.label);
                          } else {
                            router.push(item.path);
                            setOpenMenu(null);
                          }
                        }}
                        className={`w-full 
              flex items-center gap-4 px-4 py-3 rounded-lg
              text-sm font-medium transition-all
              ${isActiveParent
                            ? "bg-zinc-800 text-white"
                            : "text-slate-400 hover:bg-zinc-900 hover:text-white"}
            `}
                      >
                        <Icon className="w-5 h-5" />
                        {item.label}
                      </button>

                      {/* Child Menu */}
                      {isOpen && item.children && (
                        <div className="ml-10 mt-1 flex flex-col gap-1">
                          {item.children.map((child, cIdx) => {
                            const isActiveChild = pathname === child.path;

                            return (
                              <button
                                key={cIdx}
                                onClick={() => router.push(child.path)}
                                className={`
                                text-left px-2 py-2 rounded-md text-sm rounded-lg transition-all
                                ${isActiveChild
                                    ? "text-white bg-zinc-800/60"
                                    : "text-slate-300 hover:text-white hover:bg-zinc-700/20"
                                  }
                              `}
                              >
                                • {child.label}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* SECTION LABEL */}
                <p className="mt-8 mb-3 text-xs tracking-widest text-slate-500 uppercase">
                  Collections
                </p>

                {collectionItems.map((item, idx) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.path;

                  return (
                    <button
                      key={idx}
                      onClick={() => router.push(item.path)}
                      className={`
              flex items-center gap-4 px-4 py-3 rounded-xl
              text-sm font-medium transition-all
              ${isActive
                          ? "bg-zinc-800 text-white"
                          : "text-slate-400 hover:bg-zinc-900 hover:text-white"}
            `}
                    >
                      <Icon className="w-5 h-5" />
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </aside>

          {/* Mobile Overlay */}
          <div
            onClick={() => setSidebarOpen(false)}
            className={`
              fixed inset-0 bg-black/50 backdrop-blur-sm z-40
              lg:hidden transition-all duration-300
              ${isSidebarOpen ? "opacity-100 bg-black visible" : "opacity-0 invisible"}
            `}
          />

          {/* Content */}
          <div className="flex-1 flex flex-col">

            {/* Header */}
            <header className="border-b border-zinc-800 bg-black/40 backdrop-blur-xl">
              <button onClick={() => setSidebarOpen(true)} className="lg:hidden">
                <Menu className="w-7 h-7 text-black mt-4" />
              </button>
            </header>

            <main className="flex-1 overflow-y-auto scrollbar-hide [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {children}
            </main>

            {/* Footer */}
            {/* <footer className="border-t border-zinc-800 bg-black">
              <p className="text-Black text-center text-lg ">
                © {new Date().getFullYear()} Developed and Designed by PremitiveKey
              </p>
            </footer> */}
          </div>
        </div>
      </div>
    </div>
  );
}
