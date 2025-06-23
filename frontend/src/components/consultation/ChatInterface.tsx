/**
 * ChatInterface component for HealthConnect AI
 * Real-time chat for consultations with file sharing
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useConsultationStore } from '@/store/consultationStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { ConsultationMessage } from '@/types/consultation';
import { 
  Send, 
  Paperclip, 
  Image, 
  FileText, 
  Download,
  X,
  Check,
  CheckCheck,
  Clock,
  AlertCircle
} from 'lucide-react';
import { clsx } from 'clsx';

interface ChatInterfaceProps {
  consultationId: string;
  currentUserId: string;
  currentUserRole: 'patient' | 'provider';
  className?: string;
}

interface FileUpload {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  url?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  consultationId,
  currentUserId,
  currentUserRole,
  className
}) => {
  const [messageText, setMessageText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [fileUploads, setFileUploads] = useState<FileUpload[]>([]);
  const [dragOver, setDragOver] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    messages,
    participants,
    sendConsultationMessage
  } = useConsultationStore();

  const { isConnected } = useWebSocket();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [messageText]);

  const handleSendMessage = async () => {
    if (!messageText.trim() && fileUploads.length === 0) return;

    try {
      const attachments = fileUploads
        .filter(upload => upload.status === 'completed')
        .map(upload => ({
          id: upload.id,
          filename: upload.file.name,
          fileType: upload.file.type,
          fileSize: upload.file.size,
          url: upload.url!,
          uploadedBy: currentUserId,
          uploadedAt: new Date().toISOString(),
          category: getFileCategory(upload.file.type)
        }));

      await sendConsultationMessage({
        consultationId,
        senderId: currentUserId,
        senderRole: currentUserRole,
        messageType: attachments.length > 0 ? 'file' : 'text',
        content: messageText.trim(),
        attachments: attachments.length > 0 ? attachments : undefined
      });

      setMessageText('');
      setFileUploads([]);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    Array.from(files).forEach(file => {
      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        alert(`File ${file.name} is too large. Maximum size is 10MB.`);
        return;
      }

      // Validate file type
      const allowedTypes = [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ];

      if (!allowedTypes.includes(file.type)) {
        alert(`File type ${file.type} is not allowed.`);
        return;
      }

      const uploadId = `upload-${Date.now()}-${Math.random()}`;
      const newUpload: FileUpload = {
        id: uploadId,
        file,
        progress: 0,
        status: 'uploading'
      };

      setFileUploads(prev => [...prev, newUpload]);
      uploadFile(newUpload);
    });
  };

  const uploadFile = async (upload: FileUpload) => {
    try {
      // Simulate file upload progress
      const formData = new FormData();
      formData.append('file', upload.file);
      formData.append('consultationId', consultationId);

      // In a real implementation, this would upload to S3 or similar
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setFileUploads(prev => prev.map(f => 
          f.id === upload.id ? { ...f, progress } : f
        ));
      }

      // Mark as completed with mock URL
      const mockUrl = `https://example.com/uploads/${upload.file.name}`;
      setFileUploads(prev => prev.map(f => 
        f.id === upload.id 
          ? { ...f, status: 'completed', url: mockUrl, progress: 100 }
          : f
      ));
    } catch (error) {
      setFileUploads(prev => prev.map(f => 
        f.id === upload.id ? { ...f, status: 'error' } : f
      ));
    }
  };

  const removeFileUpload = (uploadId: string) => {
    setFileUploads(prev => prev.filter(f => f.id !== uploadId));
  };

  const getFileCategory = (mimeType: string): string => {
    if (mimeType.startsWith('image/')) return 'medical_image';
    if (mimeType === 'application/pdf') return 'document';
    return 'other';
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return Image;
    return FileText;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getMessageStatus = (message: ConsultationMessage) => {
    const isOwnMessage = message.senderId === currentUserId;
    if (!isOwnMessage) return null;

    const readByOthers = message.readBy.filter(r => r.userId !== currentUserId);
    if (readByOthers.length === 0) return <Clock className="w-3 h-3 text-gray-400" />;
    if (readByOthers.length === 1) return <Check className="w-3 h-3 text-gray-400" />;
    return <CheckCheck className="w-3 h-3 text-blue-500" />;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const otherParticipants = participants.filter(p => p.userId !== currentUserId);

  return (
    <Card className={clsx('flex flex-col h-full', className)}>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center justify-between">
          <span>Consultation Chat</span>
          <div className="flex items-center space-x-2">
            <div className={clsx('w-2 h-2 rounded-full', {
              'bg-green-500': isConnected,
              'bg-red-500': !isConnected
            })} />
            <span className="text-sm text-gray-600">
              {otherParticipants.length} participant{otherParticipants.length !== 1 ? 's' : ''}
            </span>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages */}
        <div 
          className="flex-1 overflow-y-auto p-4 space-y-4"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Send className="w-8 h-8 text-gray-400" />
              </div>
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            messages.map((message) => {
              const isOwnMessage = message.senderId === currentUserId;
              const participant = participants.find(p => p.userId === message.senderId);
              
              return (
                <div
                  key={message.id}
                  className={clsx('flex', {
                    'justify-end': isOwnMessage,
                    'justify-start': !isOwnMessage
                  })}
                >
                  <div
                    className={clsx('max-w-[70%] rounded-lg px-4 py-3', {
                      'bg-primary-600 text-white': isOwnMessage,
                      'bg-gray-100 text-gray-900': !isOwnMessage
                    })}
                  >
                    {!isOwnMessage && (
                      <p className="text-xs font-medium mb-1 opacity-75">
                        {participant?.name || message.senderRole}
                      </p>
                    )}
                    
                    {message.content && (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                    
                    {/* File Attachments */}
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {message.attachments.map((attachment) => {
                          const FileIcon = getFileIcon(attachment.fileType);
                          return (
                            <div
                              key={attachment.id}
                              className={clsx('flex items-center space-x-2 p-2 rounded', {
                                'bg-primary-700': isOwnMessage,
                                'bg-gray-200': !isOwnMessage
                              })}
                            >
                              <FileIcon className="w-4 h-4" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">
                                  {attachment.filename}
                                </p>
                                <p className="text-xs opacity-75">
                                  {formatFileSize(attachment.fileSize)}
                                </p>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(attachment.url, '_blank')}
                                className={clsx('p-1', {
                                  'text-white hover:bg-primary-800': isOwnMessage,
                                  'text-gray-600 hover:bg-gray-300': !isOwnMessage
                                })}
                              >
                                <Download className="w-3 h-3" />
                              </Button>
                            </div>
                          );
                        })}
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs opacity-75">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                      {getMessageStatus(message)}
                    </div>
                  </div>
                </div>
              );
            })
          )}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg px-4 py-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* File Upload Preview */}
        {fileUploads.length > 0 && (
          <div className="border-t p-4 bg-gray-50">
            <div className="space-y-2">
              {fileUploads.map((upload) => {
                const FileIcon = getFileIcon(upload.file.type);
                return (
                  <div key={upload.id} className="flex items-center space-x-3 p-2 bg-white rounded border">
                    <FileIcon className="w-5 h-5 text-gray-600" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{upload.file.name}</p>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className={clsx('h-2 rounded-full transition-all', {
                              'bg-blue-500': upload.status === 'uploading',
                              'bg-green-500': upload.status === 'completed',
                              'bg-red-500': upload.status === 'error'
                            })}
                            style={{ width: `${upload.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{upload.progress}%</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFileUpload(upload.id)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex items-end space-x-2">
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none min-h-[40px] max-h-32"
                rows={1}
              />
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,.pdf,.doc,.docx,.txt"
              onChange={(e) => handleFileSelect(e.target.files)}
              className="hidden"
            />
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="flex-shrink-0"
            >
              <Paperclip className="w-4 h-4" />
            </Button>
            
            <Button
              onClick={handleSendMessage}
              disabled={!messageText.trim() && fileUploads.length === 0}
              className="flex-shrink-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          
          {!isConnected && (
            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-sm flex items-center space-x-2">
              <AlertCircle className="w-4 h-4" />
              <span>Connection lost. Messages will be sent when reconnected.</span>
            </div>
          )}
        </div>

        {/* Drag and Drop Overlay */}
        {dragOver && (
          <div className="absolute inset-0 bg-blue-500 bg-opacity-20 border-2 border-dashed border-blue-500 flex items-center justify-center">
            <div className="text-center text-blue-700">
              <Paperclip className="w-12 h-12 mx-auto mb-2" />
              <p className="text-lg font-medium">Drop files here to upload</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ChatInterface;
