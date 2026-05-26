import { LitElement } from 'lit';
export declare class DtekOutageCard extends LitElement {
    hass: any;
    private config;
    private _activeTab;
    static styles: import("lit").CSSResult;
    setConfig(config: any): void;
    _findScheduleEntity(): string | null;
    render(): import("lit-html").TemplateResult<1>;
}
