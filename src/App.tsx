import { BrowserRouter } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { ThemeProvider } from "./contexts/theme";
import { HomePage } from "./pages/HomePage";
import { environment } from "./config/environment/environment";

export function App() {
  const theme: "light" | "dark" = environment.THEME;
  return (
    <BrowserRouter>
        <ThemeProvider defaultTheme={theme}>
          <Toaster
            position="bottom-left"
            duration={3000}
            theme={theme}
            closeButton
          />
          <HomePage />
        </ThemeProvider>
    </BrowserRouter>
  );
}