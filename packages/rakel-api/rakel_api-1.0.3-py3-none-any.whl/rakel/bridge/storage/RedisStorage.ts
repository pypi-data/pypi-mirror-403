/**
 * . mochimochi . [ DATA :: RedisStorage ]
 * (  .  )  fast & soft persistence
 * o . . . o
 */

import type { AuthenticationCreds, SignalDataTypeMap, SignalKeyStore } from '../../Types/Auth'
import { BufferJSON } from '../generics'
import type { StorageProvider } from './StorageProvider'

export class RedisStorage implements StorageProvider {
    private redis: any // ioredis instance
    private prefix: string

    constructor(redisInstance: any, prefix: string = 'rakel:') {
        this.redis = redisInstance
        this.prefix = prefix
    }

    async saveCreds(creds: AuthenticationCreds): Promise<void> {
        // . action
        await this.redis.set(
            `${this.prefix}creds`,
            JSON.stringify(creds, BufferJSON.replacer)
        )
    }

    async loadCreds(): Promise<AuthenticationCreds | null> {
        // . action
        const data = await this.redis.get(`${this.prefix}creds`)
        if (!data) return null

        // . sweet return
        return JSON.parse(data, BufferJSON.reviver)
    }

    getKeys(): SignalKeyStore {
        // . return
        return {
            get: async (type, ids) => {
                const data: { [id: string]: SignalDataTypeMap[typeof type] } = {}
                await Promise.all(
                    ids.map(async id => {
                        const key = `${this.prefix}${type}:${id}`
                        const val = await this.redis.get(key)
                        if (val) {
                            data[id] = JSON.parse(val, BufferJSON.reviver)
                        }
                    })
                )
                return data
            },
            set: async (data) => {
                const pipeline = this.redis.pipeline()
                for (const category in data) {
                    for (const id in data[category as keyof SignalDataTypeMap]) {
                        const value = data[category as keyof SignalDataTypeMap]![id]
                        const key = `${this.prefix}${category}:${id}`

                        if (value) {
                            pipeline.set(key, JSON.stringify(value, BufferJSON.replacer))
                        } else {
                            pipeline.del(key)
                        }
                    }
                }
                await pipeline.exec()
            }
        }
    }

    async saveFlow(jid: string, state: any): Promise<void> {
        // . action
        await this.redis.set(
            `${this.prefix}flow:${jid}`,
            JSON.stringify(state)
        )
    }

    async loadFlow(jid: string): Promise<any | null> {
        // . action
        const data = await this.redis.get(`${this.prefix}flow:${jid}`)
        if (!data) return null
        return JSON.parse(data)
    }

    async deleteFlow(jid: string): Promise<void> {
        // . action
        await this.redis.del(`${this.prefix}flow:${jid}`)
    }
}
