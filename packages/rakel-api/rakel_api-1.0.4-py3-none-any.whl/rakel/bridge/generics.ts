/**
 * . mochimochi . [ UTIL :: generics ]
 * (  .  )  cute code & soft logic
 * o . . . o
 */

import { Boom } from '@hapi/boom'
import { createHash, randomBytes } from 'crypto'
import { proto } from '../../WAProto/index.js'
import type {
	RakelEventEmitter,
	RakelEventMap,
	ConnectionState,
	WACallUpdateType,
	WAMessageKey,
	WAVersion
} from '../Types'
import { DisconnectReason } from '../Types'
import { type BinaryNode, getAllBinaryNodeChildren, jidDecode } from '../WABinary'
import { sha256 } from './crypto'

const rakelVersion: WAVersion = [2, 3000, 1027934701]


export const BufferJSON = {
	// . action
	replacer: (k: any, value: any) => {
		if (Buffer.isBuffer(value) || value instanceof Uint8Array || value?.type === 'Buffer') {
			return { type: 'Buffer', data: Buffer.from(value?.data || value).toString('base64') }
		}
		return value
	},

	reviver: (_: any, value: any) => {
		if (isBufferObject(value)) return Buffer.from(value.data, 'base64')
		if (isNumericObject(value)) return Buffer.from(Object.values(value))
		return value
	}
}


function isBufferObject(v: any) {
	return typeof v === 'object' && v !== null && v.type === 'Buffer' && typeof v.data === 'string'
}


function isNumericObject(v: any) {
	if (typeof v !== 'object' || v === null || Array.isArray(v)) return false
	const keys = Object.keys(v)
	return keys.length > 0 && keys.every(k => !isNaN(parseInt(k, 10))) && Object.values(v).every(v => typeof v === 'number')
}


export const unixTimestampSeconds = (date: Date = new Date()) => Math.floor(date.getTime() / 1000)


export const delay = (ms: number) => delayCancellable(ms).delay


export const delayCancellable = (ms: number) => {
	// . action
	const stack = new Error().stack
	let timeout: NodeJS.Timeout
	let reject: (error: any) => void

	const promise: Promise<void> = new Promise((res, rej) => {
		timeout = setTimeout(res, ms)
		reject = rej
	})

	const cancel = () => {
		clearTimeout(timeout)
		reject(new Boom('Cancelled', { statusCode: 500, data: { stack } }))
	}

	// . sweet return
	return { delay: promise, cancel }
}


export const generateMessageID = () => '3EB0' + randomBytes(18).toString('hex').toUpperCase()


export const generateRegistrationId = (): number => {
	return ((Math.random() * 16380) | 0) + 1
}


export const generateMessageIDV2 = (userId?: string): string => {
	// . action
	const data = Buffer.alloc(8 + 20 + 16)
	data.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 1000)))

	if (userId) {
		const id = jidDecode(userId)
		if (id?.user) {
			data.write(id.user, 8)
			data.write('@c.us', 8 + id.user.length)
		}
	}

	randomBytes(16).copy(data, 28)
	const hash = createHash('sha256').update(data).digest()

	// . sweet return
	return '3EB0' + hash.toString('hex').toUpperCase().substring(0, 18)
}


export function bindWaitForEvent<T extends keyof RakelEventMap>(ev: RakelEventEmitter, event: T) {
	// . action
	return async (check: (u: RakelEventMap[T]) => Promise<boolean | undefined>, timeoutMs?: number) => {
		let l1: any, l2: any

		await promiseTimeout<void>(timeoutMs, (res, rej) => {
			l2 = (s: any) => s.connection === 'close' && rej(s.lastDisconnect?.error || new Boom('Closed', { statusCode: 501 }))
			ev.on('connection.update', l2)

			l1 = async (u: any) => (await check(u)) && res()
			ev.on(event, l1)
		}).finally(() => {
			ev.off(event, l1)
			ev.off('connection.update', l2)
		})
	}
}


export async function promiseTimeout<T>(ms: number | undefined, promise: (res: any, rej: any) => void) {
	// . action
	if (!ms) return new Promise(promise)

	const { delay, cancel } = delayCancellable(ms)
	return new Promise((res, rej) => {
		delay.then(() => rej(new Boom('Timed Out', { statusCode: 408 }))).catch(rej)
		promise(res, rej)
	}).finally(cancel) as Promise<T>
}


export const trimUndefined = (obj: any) => {
	// . action
	for (const key in obj) {
		if (typeof obj[key] === 'undefined') delete obj[key]
	}
	return obj
}


export const getKeyAuthor = (key: WAMessageKey | undefined, meId?: string) => {
	// . check
	if (!key) return ''

	// . action
	return (key.fromMe ? meId : key.participant || key.remoteJid) || ''
}


export const encodeBigEndian = (e: number, t = 4) => {
	let r = e
	const a = new Uint8Array(t)
	for (let i = t - 1; i >= 0; i--) {
		a[i] = 255 & r
		r >>>= 8
	}

	return a
}


export const getCallStatusFromNode = ({ tag, attrs }: BinaryNode) => {
	let status: WACallUpdateType
	switch (tag) {
		case 'offer':
		case 'offer_notice':
			status = 'offer'
			break
		case 'terminate':
			status = attrs.reason === 'timeout' ? 'timeout' : 'terminate'
			break
		case 'reject':
			status = 'reject'
			break
		case 'accept':
			status = 'accept'
			break
		default:
			status = 'ringing'
			break
	}

	return status
}


const STATUS_MAP: { [_: string]: proto.WebMessageInfo.Status } = {
	sender: proto.WebMessageInfo.Status.SERVER_ACK,
	played: proto.WebMessageInfo.Status.PLAYED,
	read: proto.WebMessageInfo.Status.READ,
	'read-self': proto.WebMessageInfo.Status.READ
}


export const getStatusFromReceiptType = (type: string | undefined) => {
	const status = STATUS_MAP[type!]
	if (typeof type === 'undefined') {
		return proto.WebMessageInfo.Status.DELIVERY_ACK
	}

	return status
}


export const toNumber = (t: any): number =>
	typeof t === 'object' && t ? (t.toNumber ? t.toNumber() : t.low) : t || 0
