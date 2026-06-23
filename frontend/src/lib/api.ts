const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export interface RecommendRequest {
  location: string;
  budget: "low" | "medium" | "high";
  cuisine?: string;
  min_rating?: number;
  rest_type?: string;
  online_order?: boolean;
  book_table?: boolean;
  additional?: string;
}

export interface RecommendationItem {
  rank: number;
  name: string;
  cuisines: string[];
  rating: number | null;
  votes: number;
  cost_for_two: number | null;
  budget_tier: string;
  rest_type: string | null;
  online_order: boolean;
  book_table: boolean;
  explanation: string;
}

export interface FiltersMeta {
  applied: Record<string, any>;
  relaxed: string[];
}

export interface RecommendResponse {
  summary: string | null;
  recommendations: RecommendationItem[];
  metadata: Record<string, any>;
  filters: FiltersMeta;
}

export const fetchLocations = async (): Promise<string[]> => {
  try {
    const res = await fetch(`${API_BASE_URL}/locations`);
    if (!res.ok) throw new Error("Failed to fetch locations");
    const data = await res.json();
    return data.locations || [];
  } catch (error) {
    console.error("Error fetching locations:", error);
    return [];
  }
};

export const fetchCuisines = async (): Promise<string[]> => {
  try {
    const res = await fetch(`${API_BASE_URL}/cuisines`);
    if (!res.ok) throw new Error("Failed to fetch cuisines");
    const data = await res.json();
    return data.cuisines || [];
  } catch (error) {
    console.error("Error fetching cuisines:", error);
    return [];
  }
};

export const fetchRestTypes = async (): Promise<string[]> => {
  try {
    const res = await fetch(`${API_BASE_URL}/rest-types`);
    if (!res.ok) throw new Error("Failed to fetch restaurant types");
    const data = await res.json();
    return data.rest_types || [];
  } catch (error) {
    console.error("Error fetching rest types:", error);
    return [];
  }
};

export const getRecommendations = async (
  request: RecommendRequest
): Promise<RecommendResponse> => {
  const res = await fetch(`${API_BASE_URL}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to fetch recommendations");
  }

  return await res.json();
};
