/**
 * . mochimochi . [ DATA :: StorageProvider ]
 * (  .  )  generic persistence interface
 * o . . . o
 */

import type { AuthenticationCreds, SignalKeyStore } from '../../Types/Auth'

export interface StorageProvider {
    /** Save authentication credentials (creds.json) */
    saveCreds(creds: AuthenticationCreds): Promise<void>

    /** Load authentication credentials */
    loadCreds(): Promise<AuthenticationCreds | null>

    /** Get a key-value store implementation for signal keys */
    getKeys(): SignalKeyStore

    /** Save flow state */
    saveFlow(jid: string, state: any): Promise<void>

    /** Load flow state */
    loadFlow(jid: string): Promise<any | null>

    /** Delete flow state */
    deleteFlow(jid: string): Promise<void>
}

/** 
 * Type for storage data keys used by Rakel 
 * This helps us map categories like 'pre-key', 'session', etc.
 */
export type StorageCategory = 'pre-key' | 'session' | 'sender-key' | 'app-state-sync-key' | 'app-state-sync-version' | 'contact'
