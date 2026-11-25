import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ChatAssistantComponent } from './chat-assistant.component';

import { MarkdownModule } from 'ngx-markdown';

import { provideHttpClient } from '@angular/common/http';

import { provideHttpClientTesting } from '@angular/common/http/testing';

import { TranslateModule, TranslateLoader } from '@ngx-translate/core';

import { Observable, of } from 'rxjs';

/**
 * Init the TranslateModule with TranslateLoader to empty
 */
export class MockTranslateLoader implements TranslateLoader {
  getTranslation(lang: string): Observable<any> {
    return of({});
  }
}

describe('ChatAssitantComponent', () => {
  let component: ChatAssistantComponent;
  let fixture: ComponentFixture<ChatAssistantComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        TranslateModule.forRoot({
          loader: { provide: TranslateLoader, useClass: MockTranslateLoader },
        }),
        MarkdownModule.forRoot(),
      ],
      providers: [
        provideHttpClient(), 
        provideHttpClientTesting()
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatAssistantComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('sanitizeChatHistory', () => {
    // Access the private method for unit testing
    function sanitize(response: any[]): any[] {
      return (component as any).sanitizeChatHistory(response);
    }

    // The method skips leading messages until the first 'model' role, so every
    // fixture starts with a model message (mirrors the real seeded history).
    const WELCOME = { role: 'model', content: '¡Hola! Soy AgrIA.' };

    it('should strip the ###DESCRIBE tag and keep a well-formed code block', () => {
      // Simulates the exact payload built by the backend for a parcel description:
      // "###DESCRIBE_LONG_IMAGE###\n<indication>\n\nVisual Analysis Report of Parcel: <desc>\n\n```FECHA: ...\nCULTIVO: ...\n```"
      const rawUserMsg =
        '###DESCRIBE_LONG_IMAGE###\n' +
        'Estas son las características de la parcela cuya imagen te paso.\n\n' +
        'Visual Analysis Report of Parcel: Parcela irregular con cultivo de secano.\n\n' +
        '```FECHA: 2024-07-01\nCULTIVO: Maíz\n```';

      const result = sanitize([
        WELCOME,
        { role: 'user', content: rawUserMsg },
        { role: 'model', content: 'Informe generado correctamente.' },
      ]);

      const userMsg = result.find(m => m.content.includes('FECHA'));
      expect(userMsg).toBeTruthy();

      // The user message must no longer contain the routing tag
      expect(userMsg.content).not.toContain('###DESCRIBE');
      expect(userMsg.content).not.toContain('Visual Analysis Report of Parcel');

      // It must be a single, well-formed fenced code block (exactly 3 backticks
      // per fence, no doubled closing fence)
      const fenceCount = (userMsg.content.match(/```/g) || []).length;
      expect(fenceCount).toBe(2);
      expect(userMsg.content.startsWith('```')).toBeTrue();
      expect(userMsg.content.endsWith('\n```')).toBeTrue();
      expect(userMsg.content).toContain('FECHA: 2024-07-01');
      expect(userMsg.content).toContain('CULTIVO: Maíz');

      // The model message is untouched
      expect(result[result.length - 1].content).toBe('Informe generado correctamente.');
    });

    it('should handle the short-description tag variant', () => {
      const rawUserMsg =
        '###DESCRIBE_SHORT_IMAGE###\n' +
        'These are the parcel features.\n\n' +
        '```DATE: 2024-01-15\nLAND USE: Vine\n```';

      const result = sanitize([WELCOME, { role: 'user', content: rawUserMsg }]);

      const userMsg = result.find(m => m.content.includes('DATE'));
      expect(userMsg).toBeTruthy();
      expect(userMsg.content).not.toContain('###DESCRIBE');
      const fenceCount = (userMsg.content.match(/```/g) || []).length;
      expect(fenceCount).toBe(2);
      expect(userMsg.content).toContain('DATE: 2024-01-15');
    });

    it('should leave messages without the DESCRIBE tag unchanged', () => {
      const result = sanitize([
        WELCOME,
        { role: 'user', content: '¿Cuánto pagan por la cubierta vegetal?' },
        { role: 'model', content: 'El pago es de 45,94 €/ha.' },
      ]);

      expect(result.some(m => m.content === '¿Cuánto pagan por la cubierta vegetal?')).toBeTrue();
      expect(result[result.length - 1].content).toBe('El pago es de 45,94 €/ha.');
    });

    it('should truncate markdown PDF payloads at the ```markdown fence', () => {
      const rawUserMsg =
        'Revisa este documento\n---\n### PDF CONTEXT ###\n```markdown\nPAGE 1\ntexto del pdf\n```';

      const result = sanitize([WELCOME, { role: 'user', content: rawUserMsg }]);

      const userMsg = result.find(m => m.content.includes('Revisa'));
      expect(userMsg).toBeTruthy();
      expect(userMsg.content).not.toContain('```markdown');
      expect(userMsg.content).toContain('Revisa este documento');
    });
  });
});
