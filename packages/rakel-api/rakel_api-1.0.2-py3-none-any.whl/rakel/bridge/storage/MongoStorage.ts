/**
 * . mochimochi . [ DATA :: MongoStorage ]
 * (  .  )  resilient & soft persistence
 * o . . . o
 */

import type { AuthenticationCreds, SignalDataTypeMap, SignalKeyStore } from '../../Types/Auth'
import { BufferJSON } from '../generics'
import type { StorageProvider } from './StorageProvider'

export class MongoStorage implements StorageProvider {
    private collection: any // mongodb collection instance

    constructor(collectionInstance: any) {
        this.collection = collectionInstance
    }

    async saveCreds(creds: AuthenticationCreds): Promise<void> {
        // . action
        await this.collection.updateOne(
            { _id: 'creds' },
            { $set: { data: JSON.parse(JSON.stringify(creds, BufferJSON.replacer)) } },
            { upsert: true }
        )
    }

    async loadCreds(): Promise<AuthenticationCreds | null> {
        // . action
        const doc = await this.collection.findOne({ _id: 'creds' })
        if (!doc) return null

        // . sweet return
        return JSON.parse(JSON.stringify(doc.data), BufferJSON.reviver)
    }

    getKeys(): SignalKeyStore {
        // . return
        return {
            get: async (type, ids) => {
                const data: { [id: string]: SignalDataTypeMap[typeof type] } = {}
                const docs = await this.collection.find({
                    _id: { $in: ids.map(id => `${type}:${id}`) }
                }).toArray()

                docs.forEach((doc: any) => {
                    const id = doc._id.split(':')[1]
                    data[id] = JSON.parse(JSON.stringify(doc.data), BufferJSON.reviver)
                })

                return data
            },
            set: async (data) => {
                const operations: any[] = []
                for (const category in data) {
                    for (const id in data[category as keyof SignalDataTypeMap]) {
                        const value = data[category as keyof SignalDataTypeMap]![id]
                        const mongoId = `${category}:${id}`

                        if (value) {
                            operations.push({
                                updateOne: {
                                    filter: { _id: mongoId },
                                    update: { $set: { data: JSON.parse(JSON.stringify(value, BufferJSON.replacer)) } },
                                    upsert: true
                                }
                            })
                        } else {
                            operations.push({
                                deleteOne: { filter: { _id: mongoId } }
                            })
                        }
                    }
                }
                if (operations.length) await this.collection.bulkWrite(operations)
            }
        }
    }

    async saveFlow(jid: string, state: any): Promise<void> {
        // . action
        await this.collection.updateOne(
            { _id: `flow:${jid}` },
            { $set: { data: state } },
            { upsert: true }
        )
    }

    async loadFlow(jid: string): Promise<any | null> {
        // . action
        const doc = await this.collection.findOne({ _id: `flow:${jid}` })
        return doc ? doc.data : null
    }

    async deleteFlow(jid: string): Promise<void> {
        // . action
        await this.collection.deleteOne({ _id: `flow:${jid}` })
    }
}
