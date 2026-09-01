export interface User {
  id: string;
  email: string;
  full_name?: string;
  created_at: string;
}

export interface SearchProfile {
  id: string;
  name: string;
  price_min: number;
  price_max?: number;
  size_min_sqm?: number;
  size_max_sqm?: number;
  rooms_min?: number;
  rooms_max?: number;
  cities: string[];
  districts: string[];
  max_commute_minutes?: number;
  must_have_features: string[];
  nice_to_have_features: string[];
  portals: string[];
  is_active: boolean;
  created_at: string;
}

export interface Listing {
  id: string;
  portal: string;
  url: string;
  title: string;
  description?: string;
  price_total?: number;
  price_per_sqm?: number;
  size_sqm?: number;
  rooms?: number;
  city?: string;
  district?: string;
  street?: string;
  zip_code?: string;
  features: string[];
  image_urls: string[];
  available_from?: string;
  is_active: boolean;
  first_seen_at: string;
}

export interface MatchItem {
  id: string;
  score: number;
  listing: Listing;
  notified: boolean;
  created_at: string;
}

export interface Favorite {
  id: string;
  listing: Listing;
  note?: string;
  created_at: string;
}

export interface NotificationSettings {
  email_enabled: boolean;
  push_enabled: boolean;
  min_score_for_notification: number;
  max_notifications_per_day: number;
}

export interface MarketStats {
  city: string;
  district?: string;
  history: { date: string; avg_price_per_sqm: number; listing_count: number }[];
  current_avg_price_per_sqm: number;
  current_listing_count: number;
}
