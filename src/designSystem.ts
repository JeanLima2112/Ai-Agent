// designSystem.ts

// Tema Claro (cores que você já tinha)
export const lightColors = {
  primary: "#043641",
  primaryLight: "#3B82F6",
  textDark: "#1F2937",
  textLight: "#6B7280",
  background: "#F9FAFB", // Fundo principal claro
  white: "#FFFFFF",      // Cor dos cards, tabelas, etc.
  error: "#DC2626",
  success: "#16A34A",
  bluePrimary: "#043641",
  header: "#FFFFFF",
  alternateRow: "#F3F4F6", // Linha de tabela alternada mais sutil
};

// Tema Escuro (baseado na sua imagem)
export const darkColors = {
  primary: "#043641",
  primaryLight: "#3B82F6",
  textDark: "#F9FAFB", // Texto principal agora é claro
  textLight: "#9CA3AF", // Texto secundário
  background: "#111827", // Fundo principal escuro
  white: "#1F2937",      // Cor dos cards, tabelas, etc. agora é escura
  error: "#DC2626",
  success: "#16A34A",
  bluePrimary: "#043641",
  header: "#1F2937",
  alternateRow: "#374151", // Linha de tabela alternada escura
};

// O resto do design system continua igual
export const fontSizes = {
  sm: "0.875rem",
  base: "1rem",
  lg: "1.125rem",
  xl: "1.25rem",
  title: "1.5rem", // Ajustei para caber melhor no header
  xxl: '2.5rem',
};

export const spacing = {
  xs: "4px", sm: "8px", md: "16px", lg: "24px", xl: "32px",
};

export const borders = {
  radius: "8px",
};