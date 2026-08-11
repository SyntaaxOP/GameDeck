export type GameNightStatus='planned'|'completed'|'cancelled'; export type AttendeeStatus='confirmed'|'maybe'|'declined'
export interface GameNightAttendee{id:number;name:string;response:AttendeeStatus}
export interface GameNight{id:number;title:string;game_id:number|null;game_title:string|null;scheduled_at:string;duration_minutes:number;status:GameNightStatus;notes:string|null;attendees:GameNightAttendee[];created_at:string;updated_at:string}
export interface GameNightInput{title:string;game_id:number|null;scheduled_at:string;duration_minutes:number;status:GameNightStatus;notes:string|null;attendees:{name:string;response:AttendeeStatus}[]}
export interface GameNightList{items:GameNight[];total:number}
