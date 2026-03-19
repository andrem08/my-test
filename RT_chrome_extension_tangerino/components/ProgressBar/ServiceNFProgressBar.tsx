
import React, { useEffect, useState } from "react";
import CCReportProgressBarEntry from "./CCReportProgressBarEntry";

interface ProgressState {
  progress: number;
  total: number;
  label: string;
}

const ServiceNFProgressBar: React.FC = () => {
  const [progress, setProgress] = useState<ProgressState>({
    progress: 0,
    total: 0,
    label: "Starting..."
  });

  useEffect(() => {
    const listener = (changes: { [key: string]: chrome.storage.StorageChange }) => {
      if (changes.serviceNFLabelsProgress) {
        const { newValue } = changes.serviceNFLabelsProgress;
        if (newValue) {
          setProgress({
            progress: newValue.progress,
            total: newValue.total,
            label: "Pegando indices"
          });
        }
      }
      if (changes.serviceNFInfoProgress) {
        const { newValue } = changes.serviceNFInfoProgress;
        if (newValue) {
          setProgress({
            progress: newValue.progress,
            total: newValue.total,
            label: "Processando notas"
          });
        }
      }
    };

    chrome.storage.onChanged.addListener(listener);

    return () => {
      chrome.storage.onChanged.removeListener(listener);
    };
  }, []);

  return (
    <div>
      <CCReportProgressBarEntry
        label={progress.label}
        progress={progress.progress}
        total={progress.total}
      />
    </div>
  );
};

export default ServiceNFProgressBar;

export default ServiceNFProgressBar;
