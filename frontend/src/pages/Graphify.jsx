import { useState } from "react";
import UploadBox from "../components/UploadBox";
import FileList from "../components/FileList";
import GraphPanel from "../components/GraphPanel";

export default function Graphify() {
  const [files, setFiles] = useState([]);

  const handleUpload = (data) => {
    setFiles((prev) => [...prev, data.filename]);
  };

  return (
    <div className="grid h-full min-h-0 gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
      <div className="flex min-h-0 flex-col gap-5">
        <UploadBox onUpload={handleUpload} />
        <FileList files={files} />
      </div>

      <div className="min-h-[320px] lg:min-h-0">
        <GraphPanel />
      </div>
    </div>
  );
}
