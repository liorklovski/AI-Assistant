import React, { useCallback, useState } from 'react';
import { DocumentIcon } from './icons/DocumentIcon';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  disabled?: boolean;
}

export const FileUpload = ({ 
  onFileUpload, 
  disabled = false 
}: FileUploadProps) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (files && files.length > 0 && !disabled) {
      onFileUpload(files[0]);
    }
  }, [onFileUpload, disabled]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    if (!disabled) {
      const files = e.dataTransfer.files;
      handleFileSelect(files);
    }
  }, [disabled, handleFileSelect]);

  return (
    <div 
      className={`file-upload ${isDragOver ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-input"
        className="file-input"
        onChange={(e) => handleFileSelect(e.target.files)}
        disabled={disabled}
        accept=".txt,.pdf,.docx,.jpg,.jpeg,.png,.csv,.json"
      />
      <label htmlFor="file-input" className="file-upload-label">
        <DocumentIcon />
        {isDragOver ? 'Drop file here' : 'Upload File'}
      </label>
    </div>
  );
};
