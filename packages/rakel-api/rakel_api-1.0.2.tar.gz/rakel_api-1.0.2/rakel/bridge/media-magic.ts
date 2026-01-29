/**
 * . mochimochi . [ UTIL :: MediaMagic ]
 * (  .  )  soft transformations for stickers & audio
 * o . . . o
 */

import { exec } from 'child_process'
import { promisify } from 'util'
import { writeFile, readFile, unlink } from 'fs/promises'
import { join } from 'path'
import { tmpdir } from 'os'
import { randomBytes } from 'crypto'

const execPromise = promisify(exec)

export class MediaMagic {
    /** 🍡 Conveter para Sticker (WebP animado ou estático) */
    static async toSticker(buffer: Buffer): Promise<Buffer> {
        // . action
        const input = join(tmpdir(), `${randomBytes(8).toString('hex')}.tmp`)
        const output = join(tmpdir(), `${randomBytes(8).toString('hex')}.webp`)

        await writeFile(input, buffer)

        try {
            // Usa FFmpeg para garantir o redimensionamento e conversão correta para figurinha (512x512)
            await execPromise(`ffmpeg -i ${input} -vf "scale=512:512:force_original_aspect_ratio=increase,crop=512:512" -c:v libwebp -preset default -loop 0 -vsync 0 -s 512x512 ${output}`)

            const result = await readFile(output)

            // . log
            // console.log('Sticker magic applied! (☆^ー^☆)')

            await unlink(input); await unlink(output)
            return result
        } catch (err) {
            await unlink(input).catch(() => { })
            throw err
        }
    }

    /** 🎵 Converter para Áudio WhatsApp (Ogg/Opus) */
    static async toPTT(buffer: Buffer): Promise<Buffer> {
        // . action
        const input = join(tmpdir(), `${randomBytes(8).toString('hex')}.tmp`)
        const output = join(tmpdir(), `${randomBytes(8).toString('hex')}.ogg`)

        await writeFile(input, buffer)

        try {
            // Converte para OGG com codec OPUS (padrão de mensagens de voz do WA)
            await execPromise(`ffmpeg -i ${input} -c:a libopus -ac 1 -ar 48000 -compression_level 10 ${output}`)

            const result = await readFile(output)

            await unlink(input); await unlink(output)
            return result
        } catch (err) {
            await unlink(input).catch(() => { })
            throw err
        }
    }
}
