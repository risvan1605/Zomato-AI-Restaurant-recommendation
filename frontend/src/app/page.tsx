"use client";

import { useState, useEffect, FormEvent } from "react";
import {
  fetchLocations,
  fetchCuisines,
  getRecommendations,
  RecommendRequest,
  RecommendResponse,
} from "@/lib/api";

export default function Home() {
  const [started, setStarted] = useState(false);

  // Form state
  const [locations, setLocations] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);
  
  const [location, setLocation] = useState("");
  const [budgetVal, setBudgetVal] = useState<number>(1); // 0=low, 1=medium, 2=high
  const [minRating, setMinRating] = useState<number>(4.0);
  const [cuisine, setCuisine] = useState("");
  const [onlineOrder, setOnlineOrder] = useState(false);
  const [bookTable, setBookTable] = useState(false);
  const [additional, setAdditional] = useState("");

  // Results state
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLocations().then(setLocations);
    fetchCuisines().then(setCuisines);
  }, []);

  const getBudgetString = (val: number): "low" | "medium" | "high" => {
    if (val === 0) return "low";
    if (val === 1) return "medium";
    return "high";
  };

  const getBudgetDisplay = (val: number) => {
    if (val === 0) return "₹ Low (Under ₹300)";
    if (val === 1) return "₹₹ Medium (₹300 - ₹800)";
    return "₹₹₹ High (₹800+)";
  };

  const handleSearch = async (e?: FormEvent) => {
    if (e) e.preventDefault();
    if (!location) {
      setError("Please select a location.");
      return;
    }
    
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const req: RecommendRequest = {
        location,
        budget: getBudgetString(budgetVal),
        min_rating: minRating,
        cuisine: cuisine || undefined,
        online_order: onlineOrder || undefined,
        book_table: bookTable || undefined,
        additional: additional || undefined,
      };

      const res = await getRecommendations(req);
      setResponse(res);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  if (!started) {
    return (
      <main className="relative min-h-screen flex items-center justify-center pt-xl pb-xl px-md hero-bg">
        {/* TopNavBar */}
        <nav className="fixed top-0 w-full z-50 bg-surface-dim/80 backdrop-blur-xl border-b border-white/10 shadow-[0_20px_40px_rgba(15,12,41,0.4)]">
          <div className="flex justify-between items-center px-md py-xs w-full max-w-container-max mx-auto h-[72px]">
            <div className="flex items-center gap-sm">
              <span className="font-headline-md text-headline-md font-bold text-primary tracking-tight">
                Lumina Dining
              </span>
            </div>
            <div className="hidden md:flex items-center gap-lg">
              <span className="text-primary font-bold border-b-2 border-primary pb-1 font-label-md text-label-md cursor-pointer">
                Discover
              </span>
              <span className="text-on-surface-variant font-medium font-label-md text-label-md cursor-pointer hover:text-primary transition-colors">
                Collections
              </span>
              <span className="text-on-surface-variant font-medium font-label-md text-label-md cursor-pointer hover:text-primary transition-colors">
                Reservations
              </span>
            </div>
            <div className="flex items-center gap-sm">
              <div className="w-10 h-10 rounded-full bg-surface-container-high overflow-hidden border border-white/10">
                <img
                  alt="User profile"
                  className="w-full h-full object-cover"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuBghfLX8StirMxuhGvYVfPpJckLim4FcBaOQ29FsOCI72CoeNI1NKI3KWnT17AGybs4g33RE8xq_yxXz90WN3tY_BnoPBwzFz-puW3OYsnK49DzAGfakE1R9rvu8cdj5w2Kb0LhvFZyKJPs642l-h6bPKi_uzFHRQK-Wp68xWXO8Ipo0YlL0Ahq1m8dtielDJM0qrjn3muOaTcP0C-RsOK-Fsd-rZDMTTn_ljfgTo5y4FDBWJbLRicQYvcFaDGGwduC1OOyw9SfgZY"
                />
              </div>
            </div>
          </div>
        </nav>

        {/* Abstract Background Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/10 rounded-full blur-[100px]"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary-container/20 rounded-full blur-[120px]"></div>
        </div>

        <div className="relative z-10 w-full max-w-3xl mx-auto text-center flex flex-col items-center mt-12">
          {/* AI Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-container/15 border border-primary/20 backdrop-blur-md mb-lg shadow-[0_0_20px_rgba(192,193,255,0.1)]">
            <span className="material-symbols-outlined text-primary text-sm">auto_awesome</span>
            <span className="font-label-sm text-label-sm text-primary uppercase tracking-wider">
              AI Concierge Enabled
            </span>
          </div>

          <h1 className="font-headline-xl text-headline-xl md:text-[64px] md:leading-[72px] font-bold mb-md tracking-tight">
            <span className="block text-on-surface">Discover Your</span>
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary mt-2">
              Perfect Meal
            </span>
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto mb-xl">
            AI-powered restaurant recommendations tailored strictly to your palate. Experience dining curated with celestial precision.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-md">
            <button
              onClick={() => setStarted(true)}
              className="gradient-btn flex items-center justify-center gap-3 px-8 py-4 rounded-xl text-white font-label-md text-label-md font-semibold overflow-hidden relative group"
            >
              <span className="relative z-10">Get Started</span>
              <span className="material-symbols-outlined relative z-10 group-hover:translate-x-1 transition-transform duration-300">
                arrow_forward
              </span>
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden pt-[72px]">
      {/* TopNavBar */}
      <nav className="fixed top-0 w-full z-50 bg-surface-dim/80 backdrop-blur-xl border-b border-white/10 shadow-[0_20px_40px_rgba(15,12,41,0.4)]">
        <div className="flex justify-between items-center px-md py-xs w-full max-w-container-max mx-auto h-[72px]">
          <div className="flex items-center gap-sm">
            <span className="font-headline-md text-headline-md font-bold text-primary tracking-tight">
              Lumina Dining
            </span>
          </div>
          <div className="hidden md:flex items-center gap-lg">
            <span className="text-primary font-bold border-b-2 border-primary pb-1">AI Concierge</span>
          </div>
          <div className="flex items-center gap-sm">
             <div className="w-10 h-10 rounded-full bg-surface-container-high overflow-hidden border border-white/10">
                <img
                  alt="User profile"
                  className="w-full h-full object-cover"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuCXNl7w374_XZMXr0dBEmH3_t4X_ng9Id82cz3YmUJ5UR1p_dFLlhTRQkSC21dgAfqmqj2eNpWRlQAupvf1R3QaVjag4s2zRmCVyv6n6EBOv9L_QRVttVMWILD2MVIcV52x1eXZLHt843_1zoDjVGQ9YqZ49V6zRMvNGBQcI0vSoms8Xhk9EXdYkDu9xKVaqXxd0_SyzRjLzsXyibwHUb7Y-jTMBtcWgH72iFPVjVKdzV8KWfu1P99aFSpT7eBTuqSOB-oW_kM46tw"
                />
              </div>
          </div>
        </div>
      </nav>

      {/* Sidebar: Preferences */}
      <section className="w-full md:w-[320px] h-full overflow-y-auto bg-surface-container-low/30 backdrop-blur-md border-r border-white/5 p-lg custom-scrollbar shrink-0 z-10">
        <div className="flex items-center gap-2 mb-xl">
          <span className="material-symbols-outlined text-primary text-[28px]">manage_search</span>
          <h2 className="font-headline-md text-headline-md font-semibold tracking-tight text-on-surface">
            Your Preferences
          </h2>
        </div>

        <form onSubmit={handleSearch} className="space-y-6">
          {/* Location */}
          <div className="space-y-2">
            <label className="font-label-md text-label-md text-on-surface-variant block">Location *</label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/70 text-[20px]">
                location_on
              </span>
              <select
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-surface-container/40 border border-white/10 rounded-lg py-3 pl-10 pr-4 text-on-surface appearance-none focus:outline-none focus:border-primary focus:shadow-[0_0_10px_rgba(192,193,255,0.2)] transition-all font-body-md"
              >
                <option value="">Select a location...</option>
                {locations.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
              <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant/70 text-[20px] pointer-events-none">
                expand_more
              </span>
            </div>
          </div>

          {/* Budget Scroller */}
          <div className="space-y-2">
            <label className="font-label-md text-label-md text-on-surface-variant flex flex-col gap-1">
              <span>Budget Range *</span>
              <span className="text-primary font-medium">{getBudgetDisplay(budgetVal)}</span>
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="1"
              value={budgetVal}
              onChange={(e) => setBudgetVal(parseInt(e.target.value))}
              className="w-full accent-primary h-2 bg-surface-container/50 rounded-full appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-on-surface-variant px-1">
              <span>Low</span>
              <span>Medium</span>
              <span>High</span>
            </div>
          </div>

          {/* Rating Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="font-label-md text-label-md text-on-surface-variant">Minimum Rating</label>
              <span className="font-label-md text-label-md text-primary font-medium flex items-center gap-1">
                {minRating.toFixed(1)}{" "}
                <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  star
                </span>
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="5"
              step="0.5"
              value={minRating}
              onChange={(e) => setMinRating(parseFloat(e.target.value))}
              className="w-full accent-primary h-2 bg-surface-container/50 rounded-full appearance-none cursor-pointer"
            />
          </div>

          {/* Cuisine Dropdown */}
          <div className="space-y-2">
            <label className="font-label-md text-label-md text-on-surface-variant block">Cuisine Preference</label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/70 text-[20px]">
                restaurant
              </span>
              <select
                value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                className="w-full bg-surface-container/40 border border-white/10 rounded-lg py-3 pl-10 pr-4 text-on-surface appearance-none focus:outline-none focus:border-primary focus:shadow-[0_0_10px_rgba(192,193,255,0.2)] transition-all font-body-md"
              >
                <option value="">Any Cuisine</option>
                {cuisines.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant/70 text-[20px] pointer-events-none">
                expand_more
              </span>
            </div>
          </div>

          {/* Toggles */}
          <div className="space-y-4 pt-sm">
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="font-label-md text-label-md text-on-surface-variant group-hover:text-on-surface transition-colors flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">local_mall</span> Online Order
              </span>
              <div className="relative">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={onlineOrder}
                  onChange={(e) => setOnlineOrder(e.target.checked)}
                />
                <div className="w-11 h-6 bg-surface-container-high rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </div>
            </label>
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="font-label-md text-label-md text-on-surface-variant group-hover:text-on-surface transition-colors flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">event_seat</span> Book Table
              </span>
              <div className="relative">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={bookTable}
                  onChange={(e) => setBookTable(e.target.checked)}
                />
                <div className="w-11 h-6 bg-surface-container-high rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </div>
            </label>
          </div>

          {/* Additional Preferences */}
          <div className="space-y-2">
            <label className="font-label-md text-label-md text-on-surface-variant block">Additional Notes</label>
            <textarea
              value={additional}
              onChange={(e) => setAdditional(e.target.value)}
              className="w-full bg-surface-container/40 border border-white/10 rounded-lg p-3 text-on-surface focus:outline-none focus:border-primary focus:shadow-[0_0_10px_rgba(192,193,255,0.2)] transition-all font-body-md resize-none"
              placeholder="e.g., Quiet ambiance, vegan options available..."
              rows={3}
            ></textarea>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-lg gradient-btn text-white font-headline-sm py-4 rounded-xl shadow-[0_0_20px_rgba(192,193,255,0.2)] hover:shadow-[0_0_30px_rgba(192,193,255,0.4)] transition-all duration-300 flex justify-center items-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="material-symbols-outlined animate-spin">refresh</span>
            ) : (
              <span className="material-symbols-outlined group-hover:rotate-12 transition-transform">auto_awesome</span>
            )}
            {loading ? "Curating..." : "Get Recommendations"}
          </button>
        </form>
      </section>

      {/* Main Results Area */}
      <section className="flex-1 h-full p-md md:p-xl flex flex-col overflow-hidden relative">
        {error && (
          <div className="mb-md p-4 rounded-xl bg-error-container/20 border border-error/50 text-error flex items-start gap-3 backdrop-blur-md">
            <span className="material-symbols-outlined shrink-0">error</span>
            <p className="font-body-md text-sm">{error}</p>
          </div>
        )}

        {/* AI Insights Banner */}
        {response?.summary && (
          <div className="mb-xl shrink-0 relative overflow-hidden rounded-2xl bg-surface-container-high/40 backdrop-blur-xl border border-white/10 p-md shadow-[0_20px_40px_rgba(15,12,41,0.5)]">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>
            <div className="absolute inset-y-0 left-0 w-px bg-gradient-to-b from-transparent via-secondary/30 to-transparent"></div>
            <div className="flex items-start gap-md relative z-10">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center shrink-0 border border-primary/30 shadow-[0_0_15px_rgba(192,193,255,0.2)]">
                <span className="material-symbols-outlined text-primary text-[24px]">psychology</span>
              </div>
              <div>
                <h3 className="font-headline-sm text-primary mb-1 flex items-center gap-2">
                  AI Insights <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                </h3>
                <p className="font-body-md text-on-surface italic text-on-surface/90">"{response.summary}"</p>
              </div>
            </div>
          </div>
        )}

        {/* Filters Summary */}
        {response && (
          <div className="flex items-center gap-sm mb-lg overflow-x-auto pb-2 custom-scrollbar shrink-0">
            <span className="font-label-sm text-on-surface-variant uppercase tracking-wider shrink-0">Filters:</span>
            <div className="flex gap-2">
              {Object.entries(response.filters.applied).map(([key, val]) => (
                <span
                  key={key}
                  className="bg-primary/15 text-primary border border-primary/20 px-3 py-1.5 rounded-full font-label-md flex items-center gap-1 shrink-0 backdrop-blur-sm"
                >
                  <span className="capitalize">{key}:</span> {val?.toString()}
                </span>
              ))}
              {response.filters.relaxed.map((key) => (
                <span
                  key={key}
                  className="bg-error/15 text-error border border-error/20 px-3 py-1.5 rounded-full font-label-md flex items-center gap-1 shrink-0 backdrop-blur-sm"
                >
                  <span className="line-through opacity-75">{key} (Relaxed)</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Results Grid */}
        <div className="flex-1 overflow-y-auto pr-2 pb-lg custom-scrollbar">
          {!response && !loading && !error && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-60">
              <span className="material-symbols-outlined text-6xl mb-4 text-on-surface-variant">restaurant_menu</span>
              <h3 className="font-headline-sm text-on-surface">Ready to discover</h3>
              <p className="font-body-md text-on-surface-variant max-w-[400px] mt-2">
                Set your preferences on the left and let Lumina AI curate the perfect dining experience for you.
              </p>
            </div>
          )}

          {loading && (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-md">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="relative bg-white/[0.03] border border-white/10 rounded-2xl p-sm backdrop-blur-[20px] h-72 flex flex-col shadow-[0_20px_40px_rgba(15,12,41,0.3)]"
                >
                  <div className="w-full h-32 bg-surface-container/50 rounded-xl mb-4 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full animate-shimmer"></div>
                  </div>
                  <div className="h-6 w-3/4 bg-surface-container/50 rounded mb-2"></div>
                  <div className="h-4 w-1/2 bg-surface-container/50 rounded mb-auto"></div>
                </div>
              ))}
            </div>
          )}

          {response && response.recommendations.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-md">
              {response.recommendations.map((rec, idx) => (
                <article
                  key={idx}
                  className="glass-card rounded-xl flex flex-col group transition-all duration-300 hover:bg-white/[0.08]"
                >
                  {/* We removed the food image and instead use a nice gradient header */}
                  <div className="relative h-24 overflow-hidden rounded-t-xl bg-gradient-to-br from-surface-container-high to-surface-dim border-b border-white/10 flex items-center px-4">
                    <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdHRlcm4gaWQ9InNtYWxsR3JpZCIgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDEwIDAgTCAwIDAgMCAxMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIiBzdHJva2Utd2lkdGg9IjAuNSIvPjwvcGF0dGVybj48cmVjdCB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIGZpbGw9InVybCgjc21hbGxHcmlkKSIvPjxwYXRoIGQ9Ik0gNDAgMCBMIDAgMCAwIDQwIiBmaWxsPSJub25lIiBzdHJva2Utd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-20"></div>
                    <div className="absolute top-4 left-4 flex items-center justify-center w-10 h-10 rounded-full bg-surface-dim/80 backdrop-blur-md border border-white/20 shadow-lg z-10">
                      <span
                        className={`font-headline-md font-bold ${
                          rec.rank === 1
                            ? "rank-badge-gold"
                            : rec.rank === 2
                            ? "rank-badge-silver"
                            : rec.rank === 3
                            ? "rank-badge-bronze"
                            : "text-primary"
                        }`}
                      >
                        #{rec.rank}
                      </span>
                    </div>
                  </div>

                  <div className="p-sm flex-1 flex flex-col">
                    <h2 className="font-headline-md text-on-surface font-bold tracking-tight mb-2 line-clamp-1">
                      {rec.name}
                    </h2>

                    <div className="flex flex-wrap gap-2 mb-3">
                      {rec.cuisines.slice(0, 3).map((c) => (
                        <span key={c} className="px-2 py-1 rounded-full badge-glass font-label-sm text-primary">
                          {c}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center gap-4 mb-4 font-label-sm text-on-surface-variant">
                      <div className="flex items-center gap-1 text-tertiary">
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          star
                        </span>
                        <span className="font-bold text-on-surface">{rec.rating?.toFixed(1) || "-"}</span>
                        <span className="text-xs ml-1">({rec.votes})</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span>₹{rec.cost_for_two || "?"} for two</span>
                      </div>
                    </div>

                    <div className="ai-box p-3 rounded-r-lg mb-4 mt-auto">
                      <p className="font-body-md text-on-surface-variant italic text-xs">"{rec.explanation}"</p>
                    </div>

                    <div className="flex items-center justify-between mt-2 pt-3 border-t border-white/5">
                      <div className="flex gap-2 text-on-surface-variant">
                        {rec.online_order && (
                          <span className="material-symbols-outlined text-sm" title="Online Order Available">
                            local_mall
                          </span>
                        )}
                        {rec.book_table && (
                          <span className="material-symbols-outlined text-sm" title="Table Booking Available">
                            event_seat
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {response && response.recommendations.length === 0 && (
            <div className="text-center py-xl opacity-80">
              <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-2">search_off</span>
              <p className="font-body-lg text-on-surface">No restaurants found.</p>
              <p className="font-body-md text-on-surface-variant text-sm mt-1">Try adjusting your filters.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
