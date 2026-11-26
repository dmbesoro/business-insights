  import { useState } from "react";
  import { useMutation, useQueryClient } from "@tanstack/react-query";
  import { uploadReport } from "../api/reports";
  import { useUIStore } from "../stores/uiStore";

  export default function UploadPanel() {
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState("");
    const closeUploadPanel = useUIStore(
      (state) => state.closeUploadPanel
    );
    const queryClient = useQueryClient();

    const mutation = useMutation({
      mutationFn: uploadReport,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["reports"] });
        setFile(null);
        setError("");
        closeUploadPanel();
      },
      onError: () => {
        setError("Upload failed. Please try again.");
      },
    });

    function handleUpload() {
      if (!file) {
        setError("Please select a file first.");
        return;
      }

      setError("");
      mutation.mutate(file);
    }

    return (
      <section className="panel">
        <h2>Upload report</h2>

        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setError("");
          }}
        />

        {file && <p>Selected: {file.name}</p>}

        {error && <p role="alert">{error}</p>}

        {mutation.isPending && <p>Uploading report...</p>}

        <button
          type="button"
          onClick={handleUpload}
          disabled={!file || mutation.isPending}
        >
          {mutation.isPending ? "Uploading..." : "Upload"}
        </button>
      </section>
    );
  }
