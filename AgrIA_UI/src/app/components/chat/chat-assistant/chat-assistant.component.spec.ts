import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ChatAssistantComponent } from './chat-assistant.component';

describe('ChatAssitantComponent', () => {
  let component: ChatAssistantComponent;
  let fixture: ComponentFixture<ChatAssistantComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatAssistantComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatAssistantComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
