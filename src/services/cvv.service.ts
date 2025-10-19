import { api } from "@/config";

export class CVVService {
  public static async createCVV(
    file: File,
    description: string
  ): Promise<void> {
    const formData = new FormData();
    formData.append("pdf_file", file);
    formData.append("description", description);

    try {
      const response = await api.post("/cvv/create-cvv", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        responseType: "blob",
      });

      const contentDisposition = response.headers["content-disposition"] || "";
      const match = contentDisposition.match(/filename="?([^";]+)"?/i);
      const filename =
        match && match[1]
          ? match[1]
          : `${file.name.replace(/\.[^/.]+$/, "")}-CVV.pdf`;

      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Erro durante o processamento do CVV:", error);
      throw error;
    }
  }
}
