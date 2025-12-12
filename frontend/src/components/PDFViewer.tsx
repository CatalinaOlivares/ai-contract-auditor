import { useState, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

interface PDFViewerProps {
  contractId: string;
}

export default function PDFViewer({ contractId }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [loading, setLoading] = useState<boolean>(true);
  const [_error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'pdf' | 'text'>('pdf');
  const [textContent, setTextContent] = useState<string>('');

  const pdfUrl = `/api/contracts/${contractId}/pdf`;

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  }, []);

  const onDocumentLoadError = useCallback((error: Error) => {
    console.error('PDF load error:', error);
    setError('PDF not available. Showing text view.');
    setLoading(false);
    setViewMode('text');
    // Fetch text content as fallback
    fetchTextContent();
  }, [contractId]);

  const fetchTextContent = async () => {
    try {
      const response = await fetch(`/api/contracts/${contractId}/text`);
      if (response.ok) {
        const data = await response.json();
        setTextContent(data.text || 'No text available');
      }
    } catch (err) {
      setTextContent('Failed to load text content');
    }
  };

  const goToPrevPage = () => {
    setCurrentPage((prev) => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setCurrentPage((prev) => Math.min(prev + 1, numPages));
  };

  const zoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 2.5));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  // Text view fallback
  if (viewMode === 'text') {
    return (
      <div className="h-full flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-3 py-2 bg-gray-100 border-b">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('pdf')}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Try PDF View
            </button>
          </div>
          <span className="text-xs text-gray-500">Text View (PDF not available)</span>
        </div>

        {/* Text Content */}
        <div className="flex-1 overflow-auto p-4 bg-white">
          <pre className="whitespace-pre-wrap text-xs font-mono text-gray-700 bg-gray-50 p-4 rounded-lg">
            {textContent || 'Loading text...'}
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-100 border-b">
        <div className="flex items-center gap-2">
          {/* Page Navigation */}
          <button
            onClick={goToPrevPage}
            disabled={currentPage <= 1}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Previous page"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <span className="text-sm text-gray-600 min-w-[80px] text-center">
            {loading ? '...' : `${currentPage} / ${numPages}`}
          </span>

          <button
            onClick={goToNextPage}
            disabled={currentPage >= numPages}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Next page"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <div className="w-px h-5 bg-gray-300 mx-2" />

          {/* Zoom Controls */}
          <button
            onClick={zoomOut}
            disabled={scale <= 0.5}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
            title="Zoom out"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>

          <span className="text-sm text-gray-600 min-w-[50px] text-center">
            {Math.round(scale * 100)}%
          </span>

          <button
            onClick={zoomIn}
            disabled={scale >= 2.5}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
            title="Zoom in"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        {/* View Toggle */}
        <button
          onClick={() => {
            if (viewMode === 'pdf') {
              fetchTextContent();
              setViewMode('text');
            } else {
              setViewMode('pdf');
            }
          }}
          className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-200 rounded"
        >
          {viewMode === 'pdf' ? 'Show Text' : 'Show PDF'}
        </button>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-gray-200 flex justify-center">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500 flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Loading PDF...
            </div>
          </div>
        )}

        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading=""
          className="py-4"
        >
          <Page
            pageNumber={currentPage}
            scale={scale}
            className="shadow-lg"
            renderTextLayer={true}
            renderAnnotationLayer={true}
          />
        </Document>
      </div>

      {/* Page Input */}
      {numPages > 0 && (
        <div className="flex items-center justify-center gap-2 py-2 bg-gray-100 border-t text-sm">
          <span className="text-gray-600">Go to page:</span>
          <input
            type="number"
            min={1}
            max={numPages}
            value={currentPage}
            onChange={(e) => {
              const page = parseInt(e.target.value);
              if (page >= 1 && page <= numPages) {
                setCurrentPage(page);
              }
            }}
            className="w-16 px-2 py-1 border rounded text-center"
          />
        </div>
      )}
    </div>
  );
}
