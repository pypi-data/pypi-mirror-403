/**
 * . mochimochi . [ DATA :: PostgresStorage ]
 * (  .  )  reliable & relational persistence
 * o . . . o
 */

import type { AuthenticationCreds, SignalDataTypeMap, SignalKeyStore } from '../../Types/Auth'
import { BufferJSON } from '../generics'
import type { StorageProvider } from './StorageProvider'

export class PostgresStorage implements StorageProvider {
    private pool: any // pg.Pool instance
    private tableName: string

    constructor(poolInstance: any, tableName: string = 'rakel_store') {
        this.pool = poolInstance
        this.tableName = tableName
    }

    // Helper to ensure table exists (optional, or user handles it)
    async init() {
        await this.pool.query(`
            CREATE TABLE IF NOT EXISTS ${this.tableName} (
                id TEXT PRIMARY KEY,
                data JSONB
            )
        `)
    }

    async saveCreds(creds: AuthenticationCreds): Promise<void> {
        // . action
        const data = JSON.stringify(creds, BufferJSON.replacer)
        await this.pool.query(
            `INSERT INTO ${this.tableName} (id, data) VALUES ($1, $2) 
             ON CONFLICT (id) DO UPDATE SET data = $2`,
            ['creds', data]
        )
    }

    async loadCreds(): Promise<AuthenticationCreds | null> {
        // . action
        const res = await this.pool.query(
            `SELECT data FROM ${this.tableName} WHERE id = $1`,
            ['creds']
        )
        if (res.rows.length === 0) return null
        // . sweet return
        return JSON.parse(JSON.stringify(res.rows[0].data), BufferJSON.reviver)
    }

    getKeys(): SignalKeyStore {
        // . return
        return {
            get: async (type, ids) => {
                const data: { [id: string]: SignalDataTypeMap[typeof type] } = {}
                const keys = ids.map(id => `${type}:${id}`)

                const res = await this.pool.query(
                    `SELECT id, data FROM ${this.tableName} WHERE id = ANY($1)`,
                    [keys]
                )

                for (const row of res.rows) {
                    const id = row.id.split(':')[1]
                    data[id] = JSON.parse(JSON.stringify(row.data), BufferJSON.reviver)
                }
                return data
            },
            set: async (data) => {
                const client = await this.pool.connect()
                try {
                    await client.query('BEGIN')
                    for (const category in data) {
                        for (const id in data[category as keyof SignalDataTypeMap]) {
                            const value = data[category as keyof SignalDataTypeMap]![id]
                            const key = `${category}:${id}`

                            if (value) {
                                const json = JSON.stringify(value, BufferJSON.replacer)
                                await client.query(
                                    `INSERT INTO ${this.tableName} (id, data) VALUES ($1, $2)
                                     ON CONFLICT (id) DO UPDATE SET data = $2`,
                                    [key, json]
                                )
                            } else {
                                await client.query(
                                    `DELETE FROM ${this.tableName} WHERE id = $1`,
                                    [key]
                                )
                            }
                        }
                    }
                    await client.query('COMMIT')
                } catch (e) {
                    await client.query('ROLLBACK')
                    throw e
                } finally {
                    client.release()
                }
            }
        }
    }

    async saveFlow(jid: string, state: any): Promise<void> {
        // . action
        await this.pool.query(
            `INSERT INTO ${this.tableName} (id, data) VALUES ($1, $2)
             ON CONFLICT (id) DO UPDATE SET data = $2`,
            [`flow:${jid}`, JSON.stringify(state)]
        )
    }

    async loadFlow(jid: string): Promise<any | null> {
        // . action
        const res = await this.pool.query(
            `SELECT data FROM ${this.tableName} WHERE id = $1`,
            [`flow:${jid}`]
        )
        // . sweet return
        return res.rows.length ? res.rows[0].data : null
    }

    async deleteFlow(jid: string): Promise<void> {
        // . action
        await this.pool.query(
            `DELETE FROM ${this.tableName} WHERE id = $1`,
            [`flow:${jid}`]
        )
    }
}
