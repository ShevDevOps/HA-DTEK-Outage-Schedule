import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('dtek-outage-card')
export class DtekOutageCard extends LitElement {
  @property({ attribute: false }) public hass: any;
  @property({ attribute: false }) private config: any;

  // Внутрішній стан для відстеження активної вкладки (0 - Сьогодні, 1 - Завтра)
  @state() private _activeTab: number = 0;

  static styles = css`
    :host {
      --color-yes: #ffffff;
      --color-no: #333333;
      --color-maybe: #ff9800;
      --color-empty: #ffffff;
      --text-dark: #000000;
      --text-light: #ffffff;
      --border-color: #e0e0e0;
      --accent-color: var(--primary-color, #2196f3);
    }
    ha-card {
      padding: 16px;
    }
    .header {
      margin-bottom: 8px;
    }
    .title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: bold;
      font-size: 18px;
    }
    .address {
      font-size: 13px;
      color: #727272;
      margin-top: 4px;
      font-weight: normal;
    }
    
    /* Стилі вкладок (Табів) */
    .tabs-row {
      display: flex;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 16px;
      gap: 4px;
    }
    .tab-btn {
      background: none;
      border: none;
      padding: 8px 16px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
      border-bottom: 2px solid transparent;
      transition: all 0.2s ease;
    }
    .tab-btn:hover {
      color: var(--primary-text-color, #000000);
    }
    .tab-btn.active {
      color: var(--accent-color);
      border-bottom-color: var(--accent-color);
      font-weight: bold;
    }

    /* Стилі сітки годин */
    .grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 8px;
    }
    .hour-box {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .hour-label {
      font-size: 12px;
      margin-bottom: 4px;
      font-weight: 500;
    }
    .slots-container {
      display: flex;
      width: 100%;
      height: 24px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      overflow: hidden;
    }
    .half-slot {
      flex: 1;
      height: 100%;
    }
    .yes, .empty { background-color: var(--color-yes); }
    .no { background-color: var(--color-no); }
    .maybe { background-color: var(--color-maybe); }
  `;

  setConfig(config: any) {
    if (!config.autodetect && !config.entity) {
      throw new Error('Вкажіть entity або увімкніть autodetect: true');
    }
    this.config = config;
  }

  _findScheduleEntity(): string | null {
    // 1. Якщо користувач вручную прописав entity в налаштуваннях картки, віддаємо йому пріоритет
    if (this.config?.entity && this.hass.states[this.config.entity]) {
      return this.config.entity;
    }

    // 2. Автодетекція: перебираємо ВСІ сенсори в системі й шукаємо той, що має атрибут розкладу
    const detectedEntity = Object.keys(this.hass.states).find(entityId => {
      const stateObj = this.hass.states[entityId];
      // Перевіряємо, що це сенсор і в його атрибутах фізично існує об'єкт schedule або сьогоднішній графік
      return (
        entityId.startsWith('sensor.') && 
        (stateObj?.attributes?.schedule !== undefined || stateObj?.attributes?.today !== undefined)
      );
    });

    return detectedEntity || null;
  }

  render() {
    if (!this.hass) return html``;

    const entityId = this._findScheduleEntity();
    const grafikObj = (entityId && this.hass.states[entityId]) ? this.hass.states[entityId] : null;
    
    // БЕЗПЕЧНЕ ВІДНОВЛЕННЯ ДАНИХ: Якщо сенсор unavailable, заглядаємо в restored_statuses
    let attrs = grafikObj?.attributes || {};
    const isUnavailable = grafikObj?.state === 'unavailable';
    
    if (isUnavailable && attrs.restored_statuses?.attributes) {
      attrs = attrs.restored_statuses.attributes;
    }
    
    // Витягуємо групу (лише цифри)
    const rawGroup = attrs["group_id"] || "";
    const groupNumber = String(rawGroup).replace(/[^\d.]/g, "") || "—";
    
    // Формуємо статус адреси
    let address = 'Адресу не визначено';
    if (attrs["address"]) {
      address = attrs["address"];
    } else if (isUnavailable) {
      address = `Сенсор (${entityId}) тимчасово недоступний. Оновлення...`;
    } else if (entityId) {
      address = `Знайдено сенсор (${entityId}), очікування даних ДТЕК...`;
    } else {
      address = 'Сенсор розкладу не знайдено в системи';
    }

    // Визначаємо джерело розкладу
    const scheduleData = attrs["schedule"];
    let activeSchedule: any = {};

    if (this._activeTab === 0) {
      activeSchedule = (scheduleData && typeof scheduleData === 'object' && scheduleData["today"]) 
        ? scheduleData["today"] 
        : attrs;
    } else {
      activeSchedule = (scheduleData && typeof scheduleData === 'object' && scheduleData["tomorrow"]) 
        ? scheduleData["tomorrow"] 
        : {};
    }
    
    const hours = Array.from({ length: 24 }, (_, i) => i);

    return html`
      <ha-card>
        <div class="header">
          <div class="title-row">
            <span>Графік відключень</span>
            <span>Група ${groupNumber}</span>
          </div>
          <div class="address">${address}</div>
        </div>
        
        <div class="tabs-row">
          <button 
            class="tab-btn ${this._activeTab === 0 ? 'active' : ''}" 
            @click=${() => this._activeTab = 0}>
            Сьогодні
          </button>
          <button 
            class="tab-btn ${this._activeTab === 1 ? 'active' : ''}" 
            @click=${() => this._activeTab = 1}>
            Завтра
          </button>
        </div>
        
        <div class="grid">
          ${hours.map(hour => {
            const hStr = String(hour).padStart(2, '0');
            const nextH = String((hour + 1) % 24).padStart(2, '0');
            
            const key1 = `${hStr}:00-${hStr}:30`;
            const key2 = `${hStr}:30-${nextH}:00`;
            
            const status1 = String(activeSchedule[key1] || 'empty').toLowerCase();
            const status2 = String(activeSchedule[key2] || 'empty').toLowerCase();

            return html`
              <div class="hour-box">
                <div class="hour-label">${hStr}:00</div>
                <div class="slots-container">
                  <div class="half-slot ${status1}" title="${key1}"></div>
                  <div style="width: 1px; background: var(--border-color);"></div>
                  <div class="half-slot ${status2}" title="${key2}"></div>
                </div>
              </div>
            `;
          })}
        </div>
      </ha-card>
    `;
  }
}