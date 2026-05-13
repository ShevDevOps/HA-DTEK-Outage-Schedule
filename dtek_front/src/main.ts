import { LitElement, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('dtek-outage-card')
export class DtekOutageCard extends LitElement {
  @property({ attribute: false }) public hass: any;
  @property({ attribute: false }) private config: any;

  setConfig(config: any) {
    this.config = config;
  }

  render() {
    // Зверніть увагу: назва сенсора має збігатися з унікальним ID у вашому sensor.py
    const stateObj = this.hass.states[this.config.entity];
    const schedule = stateObj?.attributes?.schedule || [];

    return html`
      <ha-card header="DTEK Schedule">
        <div class="card-content">
          Група: ${stateObj?.attributes?.group_id || 'Завантаження...'}
          </div>
      </ha-card>
    `;
  }
}