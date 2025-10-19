export const environment = {
  API_URL: import.meta.env.VITE_API_URL,
  THEME: (import.meta.env.VITE_THEME as "light" | "dark") || "light",
};
