import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, MessageSquare, AlertTriangle } from 'lucide-react';

interface FileUploadProps {
    onPdfDetails: (details: string) => void;
    isUploading: boolean;
}

const FileUploadWithChatbot: React.FC<FileUploadProps> = ({ onPdfDetails }) => {
    const [processingFiles, setProcessingFiles] = useState<File[]>([]);
    const [chatMessages, setChatMessages] = useState<string[]>([]);
    const [chatInput, setChatInput] = useState<string>('');
    const [chatLoading, setChatLoading] = useState<boolean>(false);
    const [uploading, setUploading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const savedMessages = localStorage.getItem('chatMessages');
        if (savedMessages) {
            try {
                setChatMessages(JSON.parse(savedMessages));
            } catch (e) {
                console.error("Failed to parse chat history:", e);
                localStorage.removeItem('chatMessages');
                setChatMessages([]);
            }
        }
    }, []);

    useEffect(() => {
        localStorage.setItem('chatMessages', JSON.stringify(chatMessages));
    }, [chatMessages]); 

    const handleFileUpload = useCallback(async (file: File) => {
        const formData = new FormData();
        formData.append('pdf', file);

        setUploading(true);
        setError(null);
        console.log('[UPLOAD] Starting upload:', file.name);

        try {
            const response = await fetch('http://localhost:5000/upload', {
                method: 'POST',
                body: formData,
            });

            console.log('[UPLOAD] Status:', response.status);

            if (!response.ok) {
                let errorText = await response.text();
                try {
                    const errorData = JSON.parse(errorText);
                    errorText = errorData.error || errorText;
                } catch {
                }
                console.error('[UPLOAD] Error body:', errorText);
                throw new Error(`Failed to upload PDF: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log('[UPLOAD] Response:', data);

            if (data.response) {
                onPdfDetails(data.response);
            } else {
                setError('No summary received from the backend.');
            }
        } catch (error: any) {
            console.error('[UPLOAD] Error:', error.message);
            setError(`Error uploading PDF: ${error.message}`);
        } finally {
            setUploading(false);
        }
    }, [onPdfDetails]);


    const handleChatSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!chatInput.trim()) return;

        const userMessage = chatInput.trim();
        setChatMessages(prev => [...prev, `You: ${userMessage}`]);
        setChatInput('');
        setChatLoading(true);
        setError(null);

        try {
            const response = await fetch('http://localhost:5000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                let errorText = await response.text();
                try {
                    const errorData = await response.json();
                    errorText = errorData.error || errorText;
                } catch (parseError) {
                }
                console.error('[CHAT] Error body:', errorText);
                throw new Error(`Chatbot response failed: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            setChatMessages(prev => [...prev, `Bot: ${data.response}`]);
        } catch (error: any) {
            console.error('[CHAT] Error:', error.message);
            setError(`Chatbot Error: ${error.message}`);
            setChatMessages(prev => [...prev, 'Bot: Sorry, something went wrong.']);
        } finally {
            setChatLoading(false);
        }
    };

    function cn(arg0: string, arg1: string, p0: string | boolean) {
        throw new Error('Function not implemented.');
    }

    return (
        <>
            <div
                aria-label="PDF upload area"
            >
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-4 text-lg text-gray-600">
                    
                </p>
                <p className="mt-2 text-sm text-gray-500">Only PDF files supported (max 5)</p>
                {uploading && <p className="mt-2 text-blue-500">Uploading...</p>}
            </div>

            {processingFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                    {processingFiles.map(file => (
                        <div
                            key={file.name}
                            className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-200"
                        >
                            <div className="flex items-center gap-3">
                                <FileText className="h-5 w-5 text-gray-400" />
                                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                            </div>
                            {/* <Button
                                variant="ghost"
                                size="icon"
                                onClick={() =>
                                    setProcessingFiles(files => files.filter(f => f.name !== file.name))
                                }
                                aria-label={`Remove file ${file.name}`}
                            >
                                <X className="h-4 w-4 text-gray-500 hover:text-red-500" />
                            </Button> */}
                        </div> 
                    ))}
                </div>
            )}

            <div className="mt-8 p-4 border rounded-xl bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" /> Chatbot
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                    {chatMessages.map((message, index) => (
                        <p key={index} className="text-sm text-gray-800 whitespace-pre-wrap">
                            {message}
                        </p>
                    ))}
                </div>
                <form onSubmit={handleChatSubmit} className="mt-4 flex gap-2">
                    {/* <Textarea
                        value={chatInput}
                        onChange={(e: { target: { value: React.SetStateAction<string>; }; }) => setChatInput(e.target.value)}
                        placeholder="Type your message..."
                        className="flex-grow p-2 border rounded-lg resize-none"
                        aria-label="Chat input"
                        disabled={chatLoading}
                        rows={1}
                        onKeyDown={(e: React.FormEvent<Element>) => {
                            // if (e.key === 'Enter' && !e.shiftKey) {
                            //     e.preventDefault();
                            //     handleChatSubmit(e);
                            // }
                        }}
                    /> */}
                    {/* <Button
                        type="submit"
                        className={cn(
                            'px-4 py-2 rounded-lg text-white',
                            chatLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'
                        )}
                        disabled={chatLoading}
                    >
                        {chatLoading ? 'Sending...' : 'Send'}
                    </Button> */}
                </form>
            </div>
            {error && (
                <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-start gap-2">
                    <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                    <p>{error}</p>
                </div>
            )}
        </>
    );
};

export default FileUploadWithChatbot;
