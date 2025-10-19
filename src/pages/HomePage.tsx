import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Moon, Sun, Upload, Loader2, X, FileText } from "lucide-react";
import { useTheme } from '@/contexts/theme';
import { CVVService } from '@/services/cvv.service';
import { toast } from 'sonner';
import { Progress } from '@/components/ui/progress';

export function HomePage() {
  const { theme, setTheme } = useTheme();
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (selectedFile: File | null) => {
    if (!selectedFile) return setFile(null);

    if (selectedFile.type !== 'application/pdf') {
      toast.error('Formato inválido', { description: 'Envie apenas arquivos PDF.' });
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      toast.error('Arquivo muito grande', { description: 'Máximo de 10MB.' });
      return;
    }

    setFile(selectedFile);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
  };

  const removeFile = () => setFile(null);

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !description) {
      toast.error('Atenção', { description: 'Preencha todos os campos.' });
      return;
    }

    setIsLoading(true);
    const toastId = toast.loading('Processando seu currículo...');

    try {
      await CVVService.createCVV(file, description);
      toast.success('Sucesso', {
        description: 'Currículo otimizado! O download começará em breve.',
        id: toastId,
      });
    } catch (error) {
      console.error('Erro:', error);
      toast.error('Erro', {
        description: error instanceof Error ? error.message : 'Falha no processamento.',
        id: toastId,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative">
      <Button
        variant="outline"
        size="icon"
        className="absolute top-4 right-4"
        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      >
        {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>

      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">Otimizador de Currículo</CardTitle>
          <CardDescription className="text-center">
            Envie seu currículo e a descrição da vaga para otimizá-lo automaticamente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="file-upload">Seu Currículo (PDF)</Label>
              <div className="flex items-center justify-center w-full">
                <div
                  className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer ${
                    dragActive ? 'border-primary bg-accent/30' : 'border-border bg-background hover:bg-accent/10'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {!file ? (
                    <Label htmlFor="file-upload" className="flex flex-col items-center justify-center w-full h-full cursor-pointer">
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <Upload className="w-8 h-8 mb-2 text-muted-foreground" />
                        <p className="mb-2 text-sm text-muted-foreground">
                          <span className="font-semibold">Clique para enviar</span> ou arraste e solte
                        </p>
                        <p className="text-xs text-muted-foreground">PDF (máx. 10MB)</p>
                      </div>
                      <Input
                        id="file-upload"
                        type="file"
                        className="hidden"
                        accept=".pdf"
                        onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                      />
                    </Label>
                  ) : (
                    <div className="flex flex-col items-center justify-center w-full h-full p-4">
                      <div className="flex items-center justify-between w-full p-3 bg-accent/20 rounded-md">
                        <div className="flex items-center space-x-2">
                          <div className="p-2 rounded-full bg-primary/10">
                            <FileText className="w-5 h-5 text-primary" />
                          </div>
                          <div className="overflow-hidden">
                            <p className="text-sm font-medium truncate">{file.name}</p>
                            <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                          </div>
                        </div>
                        <Button type="button" variant="ghost" size="icon" className="w-8 h-8" onClick={removeFile}>
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                      <p className="mt-3 text-xs text-center text-muted-foreground">Arraste um novo arquivo para substituir</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descrição da Vaga</Label>
              <textarea
                id="description"
                rows={4}
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Cole aqui a descrição da vaga ou as habilidades desejadas..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="flex justify-center pt-4">
              <Button type="submit" disabled={isLoading} className="w-full sm:w-auto">
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processando...
                  </>
                ) : (
                  'Otimizar Currículo'
                )}
              </Button>
            </div>
          </form>

          {isLoading && (
            <div className="mt-6 space-y-2">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Processando seu currículo...</span>
                <span>Isso pode levar alguns segundos</span>
              </div>
              <Progress value={0} className="h-2" />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
