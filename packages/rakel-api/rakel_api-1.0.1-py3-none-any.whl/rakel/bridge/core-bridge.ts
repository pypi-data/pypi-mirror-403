/**
 * . mochimochi . [ CORE :: core_bridge ]
 * (  .  )  JSON-RPC bridge for Python/others
 * o . . . o
 */

import { RakelClient } from '../../packages/rakel-node/src/client/RakelClient'
import { MochiFlow } from '../../packages/rakel-node/src/flow/MochiFlow'
import type { WAMessage, ConnectionState } from '../Types'

async function startBridge() {
    const client = new RakelClient({ printQRInTerminal: true })

    // . action: Listen for JSON commands from Stdin
    process.stdin.on('data', async (buffer) => {
        try {
            const line = buffer.toString().trim()
            if (!line) return

            const { id, method, params } = JSON.parse(line)
            handleCommand(id, method, params, client)
        } catch (err) {
            sendOutput('error', { message: 'Invalid JSON command' })
        }
    })

    // . action: Forward events to Stdout
    client.on('message', (msg: WAMessage) => {
        sendOutput('event', { name: 'message', data: msg })
    })

    client.on('connection.update', (update: Partial<ConnectionState>) => {
        sendOutput('event', { name: 'connection.update', data: update })
    })

    await client.connect()
}

async function handleCommand(id: string, method: string, params: any, client: RakelClient) {
    // . action
    try {
        let result: any

        switch (method) {
            case 'sendMessage':
                result = await client.sendMessage(params.jid, params.content)
                break
            case 'sendSticker':
                // . action: Decode buffer and send magic sticker
                if (params.buffer && params.buffer.type === 'Buffer') {
                    const buffer = Buffer.from(params.buffer.data, 'base64')
                    result = await client.sendSticker(params.jid, buffer)
                }
                break

            case 'sendVoice':
                // . action: Decode buffer and send magic voice note
                if (params.buffer && params.buffer.type === 'Buffer') {
                    const buffer = Buffer.from(params.buffer.data, 'base64')
                    result = await client.sendVoice(params.jid, buffer)
                }
                break

            case 'useFlow':
                // TODO: Implement serialized flow transfer if needed
                break

            default:
                throw new Error(`Method ${method} not found`)
        }

        sendOutput('response', { id, result })
    } catch (err: any) {
        sendOutput('response', { id, error: err.message })
    }
}

function sendOutput(type: string, payload: any) {
    // . return
    console.log(JSON.stringify({ type, ...payload }))
}

startBridge()
