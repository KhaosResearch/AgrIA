import { Component, ElementRef, inject, ViewChild } from '@angular/core';
import { IChatMessage } from '../../../models/chat-assistant.model';
import { ChatAssistantService } from '../../../services/chat-assistant.service/chat-assistant.service';
import { MarkdownModule } from 'ngx-markdown';
import { NotificationService } from '../../../services/notification.service/notification.service';
import DOMPurify from 'dompurify';

@Component({
  selector: 'app-chat-assistant',
  standalone: true,
  imports: [MarkdownModule],
  templateUrl: './chat-assistant.component.html',
  styleUrl: './chat-assistant.component.css',
})
export class ChatAssistantComponent {
  // Chat History stack
  public chatHistory: IChatMessage[] = [
    {
      role: 'model',
      content:
        '¡Hola!\n\nSoy tu Asistente de Imágenes Agrícolas, ¡pero puedes llamarme **AgrIA**!\n\nMi propósito aquí es **analizar imágenes satelitales de campos de cultivo** para asistir a los agricultores en en análisis del su **uso del espacio y los recursos, así como las prácticas agrícolas**, con el fin de **asesorarles a reunir los requisitos para las subvenciones del Comité Europeo de Política Agrícola Común (CAP)**.\n\n¡Sólo tienes que subir una imagen satelital de tus campos de cultivo y nos pondremos manos a la obra!\n\nSi tiene alguna pregunta, también puede escribir en el cuadro de texto',
    },
  ];
  // Index of the first message after chat sanitizaion
  private firstIndex: number = 8;
  // Miliscendos delay to display Chat Assistant's replies
  private milisecondsDisplay: number = 3;
  // HTML element to automatically scroll to the bototm
  @ViewChild('scrollableContainer') scrollableContainer!: ElementRef;
  // Service to handle chat messages
  public chatAssistantService: ChatAssistantService = inject(ChatAssistantService);
  // Service for notifications
  private notificationService = inject(NotificationService);

  ngOnInit() {
    if (this.chatHistory.length <= 1) {
      this.chatAssistantService.loadActiveChatHistory().subscribe({
        next: (response: IChatMessage[]) => {
          this.chatHistory = this.sanitizeChatHistory(response);
          this.scrollToBottom(); // scroll to bottom after loading history
        },
        error: err => {
          console.error('Error loading chat history:', err);
          this.chatHistory.push({
            role: 'model',
            content:
              'Error 404: Chat history not found.\nNo se pudo cargar el historial de chat. Inténtelo de nuevo más tarde o comience un nuevo chat con esta conversación.',
          });
          this.scrollToBottom();
        },
      });
    } else {
      // Load chat history if it is empty or has only the initial message
      this.animateLoadingResponse(this.chatHistory[0]);
    }
  }

  ngAfterViewInit() {
    if (this.chatHistory.length > 1) {
      this.scrollToBottom(); // in case there are loaded messages
    }
  }

  /**
   * Sanitizes chat history by removing initial messages and replacing image description requests
   * @param response - Chat history response from the server
   * @returns Sanitized chat history
   */
  private sanitizeChatHistory(response: IChatMessage[]) {
    // Skip context setting messages
    let index = this.firstIndex;
    while (index < response.length && response[index].role !== 'model') {
      index++;
    }
    let sanitized_history = response.slice(index);

    // Remove image descriptions requests data
    sanitized_history = sanitized_history.filter(msg => !msg.content.includes('###DESCRIBE'));
    return sanitized_history;
  }

  /**
   * Scrolls to the bottom of the chat window
   *
   * @param timeout - Optional timeout to delay scrolling. Default: 1500 ms.
   */
  public scrollToBottom(timeout: number = 1500) {
    setTimeout(() => {
      const el = this.scrollableContainer?.nativeElement;
      el.scrollTop = el.scrollHeight;
    }, timeout);
  }

  /**
   * Adds user message to chat and gets assistant output
   * @param content - User message content
   */
  public addUserMessage(content: string) {
    if (content.length > 0) {
      const safeContent = this.sanitizeMarkdown(content);
      this.chatHistory.push({ role: 'user', content: safeContent });
      this.sendUserInput(safeContent);
      this.scrollToBottom();
    }
  }

  /**
   * Send image to assistant
   * @param imageFile - Image file to be sent to the assistant
   */
  public sendImage(imageFile: File, isDetailedDescription: boolean) {
    this.showMessageIcon();
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('isDetailedDescription', String(isDetailedDescription));

    this.chatAssistantService.sendImage(formData).subscribe({
      next: (responseText: string) => {
        this.hideMessageIcon();
        this.displayResponse(responseText);
      },
      error: err => {
        console.error('Error from assistant:', err);
        this.hideMessageIcon();

        this.notificationService.showNotification('chat-assistant.assistant-error', err.error.error, 'error', 10000);

        this.chatHistory.push({
          role: 'model',
          content:
            'Oops! Something went wrong while processing your image. Error was:\n\n' +
            err.error.error +
            '\n\nPlease try again later.',
        });
        this.scrollToBottom();
      },
    });
  }

  /**
   * Send input and pushes assistant's response to chat stack
   *
   * @param userInput - User input message
   */
  public sendUserInput(userInput: string) {
    const trimmedInput: string = userInput
      .trim()
      .replace(/[\r\n]+/g, ' ')
      .replace(/\s+/g, ' ');
    this.showMessageIcon();
    const formData = new FormData();
    formData.append('userInput', trimmedInput);

    this.chatAssistantService.sendUserInput(formData).subscribe({
      next: (responseText: string) => {
        this.hideMessageIcon();
        this.displayResponse(responseText);
      },
      error: err => {
        console.error('Error from assistant:', err);
        this.hideMessageIcon();
        this.chatHistory.push({
          role: 'model',
          content:
            'Oops! Something went wrong while processing your image. Error was:\n\n' +
            err.error.error +
            '\n\nPlease try again later.',
        });
        this.scrollToBottom();
      },
    });
  }

  /**
   * Shows message icon while waiting response
   */
  public showMessageIcon() {
    const loadingMsg: IChatMessage = { role: 'model', content: '', loading: true };
    this.chatHistory.push(loadingMsg); // Add loading indicator
    this.scrollToBottom();
  }

  /**
   * Hides message icon after response
   */
  public hideMessageIcon() {
    const last = this.chatHistory[this.chatHistory.length - 1];
    if (last.loading) {
      this.chatHistory.pop();
    }
  }

  /**
   * Displays the output message on the chat window.
   *
   * @param responseText - response from AgrIA
   */
  public displayResponse(responseText: string) {
    const safeContent = this.sanitizeMarkdown(responseText);
    console.log('LLM RESPONSE\n', responseText);

    const newMsg: IChatMessage = {
      role: 'model',
      content: safeContent,
      revealProgress: '',
    };

    if (!newMsg.content || newMsg.content.length === 0) {
      newMsg.content = 'No response received from the assistant.';
    }

    this.chatHistory.push(newMsg);
    this.animateLoadingResponse(newMsg);
    this.scrollToBottom();
  }

  /**
   * Animates assitant's output message display
   *
   * @param msg
   * @param fullText
   */
  public animateLoadingResponse(msg: IChatMessage) {
    const fullText = msg.content || '';
    let index = 0;
    const interval = setInterval(() => {
      if (index < fullText.length) {
        msg.revealProgress = fullText.slice(0, index + 1);
        index++;
      } else {
        clearInterval(interval);
        msg.revealProgress = undefined; // done animating
      }
    }, this.milisecondsDisplay); // Adjust typing speed (ms per character)
  }

  private sanitizeMarkdown(md: string): string {
    // Remove/disallow raw HTML, allow only markdown that will be converted
    return DOMPurify.sanitize(md, {
      ALLOWED_TAGS: [], // strip all HTML tags if someone injects them
      ALLOWED_ATTR: [],
    });
  }
}
