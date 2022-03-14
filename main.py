import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord
import re
from discord_components import *
import aiosqlite
from easy_pil import Editor, load_image_async, Font
# Nuevas librerias
import youtube_dl
import asyncio
import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
from gtts import gTTS
import eyed3


load_dotenv()

# Define functions

def create_player(ctx):
    player = MusicPlayer(ctx, music_queue)
    music_players.append(player)
    try:
        del music_random_playlist[ctx.guild.id]
    except:
        pass
    return player
def check_queue(ctx, opts, queue, after, on_play, loop):
    try:
        try:
            song = queue[ctx.guild.id][0]
        except IndexError:
            try:
                queue[ctx.guild.id].remove(music_now_song[ctx.guild.id])
            except:
                pass
            try:
                del music_channels[ctx.guild.id]
            except:
                pass
            music_now_song[ctx.guild.id] = None
            try:
                message = None
                for messagex in music_messages:
                    if messagex.guild.id == ctx.guild.id:
                        message = messagex
                        break
                if message:
                    music_delete_message.start(message)
            except:
                pass
            return
        if not song.is_looping:
            try:
                queue[ctx.guild.id].remove(music_now_song[ctx.guild.id])
            except:
                pass
            if len(queue[ctx.guild.id]) > 0:
                try:
                    if music_random_playlist[ctx.guild.id]:
                        song = random.choice(queue[ctx.guild.id])
                    else:
                        raise KeyError
                except KeyError:
                    song = queue[ctx.guild.id][0]
                music_now_song[ctx.guild.id] = song
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.source, **opts))
                try:
                    ctx.voice_client.play(source, after=lambda error: after(ctx, opts, queue, after, on_play, loop))
                except:
                    try:
                        del music_channels[ctx.guild.id]
                    except:
                        pass
                    music_now_song[ctx.guild.id] = None
                    try:
                        message = None
                        for messagex in music_messages:
                            if messagex.guild.id == ctx.guild.id:
                                message = messagex
                                break
                        if message:
                            music_delete_message.start(message)
                    except:
                        pass
                    return
                song = queue[ctx.guild.id][0]
                if on_play:
                    loop.create_task(on_play(ctx, song))
            else:
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                music_now_song[ctx.guild.id] = None
                try:
                    queue[ctx.guild.id].remove(music_now_song[ctx.guild.id])
                except:
                    pass
                try:
                    message = None
                    for messagex in music_messages:
                        if messagex.guild.id == ctx.guild.id:
                            message = messagex
                            break
                    if message:
                        music_delete_message.start(message)
                except Exception as e:
                    print(e)
                return
        else:
            song = queue[ctx.guild.id][0]
            music_now_song[ctx.guild.id] = song
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.source, **opts))
            try:
                ctx.voice_client.play(source, after=lambda error: after(ctx, opts, queue, after, on_play, loop))
            except:
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                music_now_song[ctx.guild.id] = None
                try:
                    message = None
                    for messagex in music_messages:
                        if messagex.guild.id == ctx.guild.id:
                            message = messagex
                            break
                    if message:
                        music_delete_message.start(message)
                except:
                    pass
                return
            song = queue[ctx.guild.id][0]
            if on_play:
                loop.create_task(on_play(ctx, song))
    except Exception as e:
        print(f'Error en la funcion \"check_queue\": {e}')
        try:
            del music_channels[ctx.guild.id]
        except:
            pass
        music_now_song[ctx.guild.id] = None
        try:
            message = None
            for messagex in music_messages:
                if messagex.guild.id == ctx.guild.id:
                    message = messagex
                    break
            if message:
                music_delete_message.start(message)
        except:
            pass
async def getPrefix(client=None, message=None):
    async with aiosqlite.connect('main.db') as db:
        async with db.cursor() as cursor:
            await cursor.execute('SELECT prefix FROM prefix_system WHERE guild = ?', (message.guild.id,))
            data = await cursor.fetchone()
            if data:
                prefix = data[0]
            else:
                prefix = '-'
        await db.commit()
    return prefix
async def _check_playlist_buttons(player, page, interaction):
    numOfSongs = 0
    songs = {}
    total_duration = 0
    for song in player.current_queue():
        total_duration += song.duration
        if numOfSongs >= int(f'{page}1') - 10:
            if numOfSongs == 0:
                pass
            elif numOfSongs < int(f'{page}1'):
                songs[song.name] = song.url
            elif numOfSongs > int(f'{page}1'):
                numOfSongs += 1
                continue
        numOfSongs += 1
    des = f'{numOfSongs - 1} canciones en espera ({str(datetime.timedelta(seconds=float(total_duration)))}):'
    num = int(f'{page - 1}1')
    if page == 1:
        num = 1
    for name, url in songs.items():
        des += f'\n`{num}` **[{name}]({url})**'
        num += 1
    
    now_song = music_now_song[interaction.guild.id]

    yf = re.findall('https://www.youtube.com/watch.v=(\w.+)', now_song.url)
    yf = f'https://img.youtube.com/vi/{yf[0]}/mqdefault.jpg'

    embed = discord.Embed(title=now_song.name, url=now_song.url, description=des, color=0xC81717)
    embed.set_author(name='Lista de reproduccion', icon_url=bot.user.avatar_url)
    embed.set_thumbnail(url=yf)

    pages = 0
    for x in range(0, numOfSongs, 10):
        pages += 1
    right = False
    left = False
    if page == pages:
                right = True
                left = False
    elif page == 1:
        left = True
        right = False
    try:
        await interaction.edit_origin(embed=embed, components=[[
                                                                    Button(style=ButtonStyle.blue, emoji='⏪', id='Sleft', disabled=left),
                                                                    Button(style=ButtonStyle.blue, emoji='⬅️', id='left', disabled=left),
                                                                    Button(style=ButtonStyle.blue, emoji='➡️', id='right', disabled=right),
                                                                    Button(style=ButtonStyle.blue, emoji='⏩', id='Sright', disabled=right)
                                                            ]])
    except:
        return None
    return True
async def check_playlist_buttons(ctx, player):
    page = 1
    while True:
        try:
            interaction = await bot.wait_for('button_click', timeout=60.0)
        except asyncio.TimeoutError:
            break
        value = interaction.component.id
        if value == 'left':
            if not ctx.voice_client:
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                await interaction.send('No estoy en ningun canal de voz!')
                break
            page -= 1
            result = await _check_playlist_buttons(player, page, interaction)
            if not result:
                break
        elif value == 'Sleft':
            if not ctx.voice_client:
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                await interaction.send('No estoy en ningun canal de voz!')
                break
            page = 1
            result = await _check_playlist_buttons(player, page, interaction)
            if not result:
                break
        elif value == 'right':
            if not ctx.voice_client:
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                await interaction.send('No estoy en ningun canal de voz!')
                break
            page += 1
            result = await _check_playlist_buttons(player, page, interaction)
            if not result:
                break
        elif value == 'Sright':
            if not ctx.voice_client:
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                await interaction.send('No estoy en ningun canal de voz!')
                break
            numOfSongs = len(player.current_queue())
            page = 0
            for x in range(0, numOfSongs, 10):
                page += 1
            result = await _check_playlist_buttons(player, page, interaction)
            if not result:
                break
async def buttons(ctx, embed):
    message = await ctx.send(embed=embed,
                             components=[[
                                                Button(style=ButtonStyle.red, label='Parar', id='stop'),
                                                Button(style=ButtonStyle.gray, label='Pausar', id='pause'),
                                                Button(style=ButtonStyle.blue, label='Saltar', id='skip'),
                                                Button(style=ButtonStyle.grey, label='Lista', id='playlist'),
                                                Button(style=ButtonStyle.blue, label='Actualizar', id='reload')
                                        ]])
    for id, channel_message in music_channels.keys():
        if id == ctx.guild.id:
            await channel_message[1].edit(components=[])
            if message in music_messages:
                try:
                    music_messages.remove(message)
                except:
                    pass
            break
    music_messages.append(message)
    music_channels[ctx.guild.id] = [ctx.message.channel.id, message]
    paused = False
    while True:
        try:
            interaction = await bot.wait_for('button_click', timeout=1800.0)
        except asyncio.TimeoutError:
            if ctx.voice_client:
                if not ctx.voice_client.is_playing() and not paused:
                    embed = discord.Embed(description='Agradeceria mucho que me recomendara a sus amigos :D', color=0xC81717)
                    embed.set_author(name='Desconectado')
                    embed.set_thumbnail(url=bot.user.avatar_url)
                    try:
                        del music_now_song[ctx.guild.id]
                    except:
                        pass
                    try:
                        await message.edit(components=[])
                    except:
                        pass
                    await ctx.voice_client.disconnect()
                    try:
                        del music_channels[ctx.guild.id]
                    except:
                        pass
                    await ctx.send(embed=embed)
                    break
        if message not in music_messages:
            try:
                await message.edit(components=[])
            except:
                pass
            break
        if not interaction.author.voice or interaction.author.voice.channel != ctx.voice_client.channel:
            await interaction.send('Debes estar en mi canal de voz')
        if not ctx.voice_client:
            try:
                del music_channels[ctx.guild.id]
            except:
                pass
            try:
                del music_now_song[ctx.guild.id]
            except:
                pass
            await interaction.message.edit(components=[])
            await interaction.send('No estoy en ningun canal de voz!')
            break
        if not ctx.voice_client.is_playing() and not paused:
            player = await get_player(ctx, True)
            if len(player.current_queue()) <= 0:
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                try:
                    del music_now_song[ctx.guild.id]
                except:
                    pass
                await interaction.message.edit(components=[])
                await interaction.send('No hay ninguna cancion en reproduccion o en lista!')
                await ctx.voice_client.disconnect()
                embed = discord.Embed(description='Agradeceria mucho que me recomendara a sus amigos :D', color=0xC81717)
                embed.set_author(name='Desconectado')
                embed.set_thumbnail(url=bot.user.avatar_url)
                
                await ctx.send(embed=embed)
                break
        else:
            value = interaction.component.id
            if value == 'stop':
                member = interaction.author 
                await ctx.voice_client.disconnect()
                try:
                    del music_channels[ctx.guild.id]
                except:
                    pass
                try:
                    del music_now_song[ctx.guild.id]
                except:
                    pass

                await interaction.message.delete()

                embed = discord.Embed(description='Agradeceria mucho que me recomendara a sus amigos :D', color=0xC81717)
                embed.set_author(name='Desconectado')
                embed.set_footer(text=f'Desconectado por: {member}')
                embed.set_thumbnail(url=bot.user.avatar_url)

                await ctx.send(embed=embed)
                break
            elif value == 'pause':
                member = interaction.author
                player = await get_player(ctx, True)
                if not ctx.voice_client.is_playing():
                    try:
                        song = await player.resume()
                        paused = False
                    except:
                        await interaction.send('No hay ninguna cancion pausada')
                        continue
                elif ctx.voice_client.is_playing():
                    try:
                        song = await player.pause()
                        paused = True
                    except:
                        await interaction.send('No hay ninguna cancion en reproduccion')
                        continue
                pausedstr = ['Pausar', 'Resumido']
                color = ButtonStyle.grey
                if paused:
                    pausedstr = ['Resumir', 'Pausado']
                    color = ButtonStyle.green

                yf = re.findall('https://www.youtube.com/watch.v=(\w.+)', song.url)
                yf = f'https://img.youtube.com/vi/{yf[0]}/mqdefault.jpg'

                prefix = await getPrefix(message=ctx)

                embed = discord.Embed(description=f'[{song.name}]({song.url})\nSi los botones no funcionan use `{prefix}nowplaying`', color=0xC81717)
                embed.set_footer(text=f'Pedida por: {song.order}\n{pausedstr[1]} por: {member}')
                embed.set_author(name='Sonando ♪', icon_url=member.avatar_url)
                embed.set_thumbnail(url=yf)

                await interaction.edit_origin(embed=embed,
                                               components=[[
                                                                Button(style=ButtonStyle.red, label='Parar', id='stop'),
                                                                Button(style=color, label=pausedstr[0], id='pause'),
                                                                Button(style=ButtonStyle.blue, label='Saltar', id='skip'),
                                                                Button(style=ButtonStyle.grey, label='Lista', id='playlist'),
                                                                Button(style=ButtonStyle.blue, label='Actualizar', id='reload')
                                                          ]])
            elif value == 'skip':
                player = await get_player(ctx, True)
                member = interaction.author
                try:    
                    song = await player.skip()
                except EmptyQueue:
                    await interaction.send('No hay ninguna cancion en la lista!')
                    continue
                except NotPlaying:
                    await interaction.send('No hay ninguna cancion en reproduccion!')
                    continue
                
                yf = re.findall('https://www.youtube.com/watch.v=(\w.+)', song.url)
                yf = f'https://img.youtube.com/vi/{yf[0]}/mqdefault.jpg'

                prefix = await getPrefix(message=ctx)

                embed = discord.Embed(description=f'[{song.name}]({song.url})\nSi los botones no funcionan use `{prefix}nowplaying`', color=0xC81717)
                embed.set_footer(text=f'Pedida por: {song.order}')
                embed.set_author(name='Sonando ♪', icon_url=member.avatar_url)
                embed.set_thumbnail(url=yf)

                await interaction.edit_origin(embed=embed,
                                               components=[[
                                                                Button(style=ButtonStyle.red, label='Parar', id='stop'),
                                                                Button(style=ButtonStyle.gray, label='Pausar', id='pause'),
                                                                Button(style=ButtonStyle.blue, label='Saltar', id='skip'),
                                                                Button(style=ButtonStyle.grey, label='Lista', id='playlist'),
                                                                Button(style=ButtonStyle.blue, label='Actualizar', id='reload')
                                                          ]])
            elif value == 'playlist':
                player = await get_player(ctx, True)
                numOfSongs = 0
                songs = {}
                total_duration = 0
                for song in player.current_queue():
                    if numOfSongs >= 11 or numOfSongs == 0:
                        numOfSongs += 1
                        continue
                    else:
                        songs[song.name] = song.url
                    numOfSongs += 1
                    total_duration += song.duration
                now_song = music_now_song[ctx.guild.id]
                des = f'{numOfSongs - 1} canciones en espera ({str(datetime.timedelta(seconds=float(total_duration)))}):'
                num = 1
                for name, url in songs.items():
                    des += f'\n`{num}` **[{name}]({url})**'
                    num += 1

                yf = re.findall('https://www.youtube.com/watch.v=(\w.+)', now_song.url)
                yf = f'https://img.youtube.com/vi/{yf[0]}/mqdefault.jpg'

                embed = discord.Embed(title=now_song.name, url=now_song.url, description=des, color=0xC81717)
                embed.set_author(name='Lista de reproduccion', icon_url=bot.user.avatar_url)
                embed.set_thumbnail(url=yf)

                dis = True
                if numOfSongs > 11:
                    dis = False
                await interaction.send(embed=embed, components=[[
                                                                                Button(style=ButtonStyle.blue, emoji='⏪', id='Sleft', disabled=True),
                                                                                Button(style=ButtonStyle.blue, emoji='⬅️', id='left', disabled=True),
                                                                                Button(style=ButtonStyle.blue, emoji='➡️', id='right', disabled=dis),
                                                                                Button(style=ButtonStyle.blue, emoji='⏩', id='Sright', disabled=dis)
                                                                          ]])
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    loop.create_task(check_playlist_buttons(ctx, player))
                else:
                    asyncio.run(check_playlist_buttons(ctx, player))
            elif value == 'reload':
                member = interaction.author
                song = music_now_song[ctx.guild.id]
                if not song:
                    try:
                        music_messages.remove(message)
                        await message.edit(components=[])
                    except:
                        pass
                    try:
                        del music_now_song[ctx.guild.id]
                    except:
                        pass
                    await interaction.send('Ya no hay canciones en la cola ni en reproduccion')
                    try:
                        await ctx.voice_client.disconnect()
                    except:
                        pass
                    embed = discord.Embed(description='Agradeceria mucho que me recomendara a sus amigos :D', color=0xC81717)
                    embed.set_author(name='Desconectado')
                    embed.set_footer(text=f'Desconectado por: {member}')
                    embed.set_thumbnail(url=bot.user.avatar_url)

                    await ctx.send(embed=embed)
                    break


                yf = re.findall('https://www.youtube.com/watch.v=(\w.+)', song.url)
                yf = f'https://img.youtube.com/vi/{yf[0]}/mqdefault.jpg'

                prefix = await getPrefix(message=ctx)

                embed = discord.Embed(description=f'[{song.name}]({song.url})\nSi los botones no funcionan use `{prefix}nowplaying`', color=0xC81717)
                embed.set_footer(text=f'Pedida por: {song.order}')
                embed.set_author(name='Sonando ♪', icon_url=member.avatar_url)
                embed.set_thumbnail(url=yf)
                try:
                    await interaction.message.delete()
                except:
                    pass
                try:
                    music_messages.remove(message)
                except:
                    pass    
                message = await ctx.send(embed=embed, components=[[
                                                                    Button(style=ButtonStyle.red, label='Parar', id='stop'),
                                                                    Button(style=ButtonStyle.gray, label='Pausar', id='pause'),
                                                                    Button(style=ButtonStyle.blue, label='Saltar', id='skip'),
                                                                    Button(style=ButtonStyle.grey, label='Lista', id='playlist'),
                                                                    Button(style=ButtonStyle.blue, label='Actualizar', id='reload')
                                                                 ]])
                music_messages.append(message)
async def get_player(ctx, bef=False):
    guild = ctx.guild.id
    for player in music_players:
        if player.ctx.guild.id == guild and not bef:
            #if len(player._queue) <= 0:
                #music_players.remove(player)
                #continue
            embed = discord.Embed(title='Encontre una lista de reproduccion! Quieres continuarla?', color=0xC81717)
            await ctx.send(embed=embed,
                           components=[[
                                            Button(style=ButtonStyle.red, label='Cancelar', id='cancel'),
                                            Button(style=ButtonStyle.green, label='Continuar', id='continue'),
                                            Button(style=ButtonStyle.grey, label='Nueva lista', id='new_list')
                                      ]])
            
            while True:
                interaction = await bot.wait_for('button_click')
                if interaction.author.id == ctx.author.id:
                    value = interaction.component.id
                    if value == 'cancel':
                        await interaction.message.edit(components=[])
                        await interaction.send('Comando cancelado', ephemeral=False)
                        await ctx.voice_client.disconnect()
                        return None
                    elif value == 'continue':
                        await interaction.message.edit(components=[])
                        await interaction.send('Lista de reproduccion continuada', ephemeral=False)
                        player.ctx = ctx
                        player.voice = ctx.voice_client
                        player.loop = ctx.bot.loop
                        return player
                    elif value == 'new_list':
                        await interaction.message.edit(components=[])
                        await interaction.send('Nueva lista de reproduccion creada', ephemeral=False)
                        music_players.remove(player)
                        del music_queue[ctx.guild.id]
                        player = create_player(ctx)
                        return player
                else:
                    await interaction.send('No puedes utilizar esta interaccion!')
        elif player.ctx.guild.id == guild:
            player.ctx = ctx
            player.voice = ctx.voice_client
            player.loop = ctx.bot.loop
            return player
    player = create_player(ctx)
    return player
async def _async_video_data(song, loop, ctx, ytdl, player):
    song_name = song['track']['name']
    artists = song['track']['artists']
    name = ''
    for artist in artists:
        artist = artist['name']
        if len(name) == 0:
            name += artist
        else:
            name += f', {artist}'
    name += f' - {song_name}'
    song = await _get_video_data(name, loop, ctx, ytdl)
    if not song:
        message = await ctx.send(f'La cancion `{name}` no se ha podido agregar por estar calificada como +18')
        await asyncio.sleep(5.0)
        return await message.delete()
    await player.add_to_queue(song)
async def async_video_data(items, loop, ctx, ytdl, player):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    for song in items:
        if loop and loop.is_running():
            loop.create_task(_async_video_data(song, loop, ctx, ytdl, player))
        else:
            asyncio.run(_async_video_data(song, loop, ctx, ytdl, player))
async def _get_video_data(url, loop, ctx, ytdl):
    try:
        if not re.findall('(https://\w.+)', url):
            characters = '\/:'
            url = ''.join( x for x in url if x not in characters)
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        if data is None:
            return None
        try:
            if len(data['entries']) > 1:
                try:
                    datas = data['entries']
                except KeyError or TypeError:
                    pass
                if datas is None:
                    return None
                songs = []
                for data in datas:
                    source = data["url"]
                    url = "https://www.youtube.com/watch?v="+data["id"]
                    title = data["title"]
                    description = data["description"]
                    views = data["view_count"]
                    duration = data["duration"]
                    thumbnail = data["thumbnail"]
                    channel = data["uploader"]
                    channel_url = data["uploader_url"]
                    order = ctx.author
                    songs.append(Song(source, url, title, description, views, duration, thumbnail, channel, channel_url, False, order))
                return songs
            else:
                raise
        except:
            try:
                data = data["entries"][0]
            except KeyError or TypeError:
                pass
            if data is None:
                return None
            source = data["url"]
            url = "https://www.youtube.com/watch?v="+data["id"]
            title = data["title"]
            description = data["description"]
            views = data["view_count"]
            duration = data["duration"]
            thumbnail = data["thumbnail"]
            channel = data["uploader"]
            channel_url = data["uploader_url"]
            order = ctx.author
            return Song(source, url, title, description, views, duration, thumbnail, channel, channel_url, False, order)
    except Exception as e:
        print(f'Error en la funcion \"_get_video_data\": {e}')
        return None
async def get_video_data(url, loop, ctx, play):
    spotiplay = re.findall('https://open.spotify.com/playlist/(\w+).si=\w+', url)
    spotisong = re.findall('https://open.spotify.com/track/(\w+).si=\w+', url)
    ytplaylist = re.findall('https://youtube.com/playlist.list=(\w+)', url)
    if spotiplay:
        ytdl = youtube_dl.YoutubeDL({"format": "bestaudio/best", "restrictfilenames": True, "noplaylist": True, "nocheckcertificate": True, "ignoreerrors": True, "logtostderr": False, "quiet": True, "no_warnings": True, "default_search": "auto", "source_address": "0.0.0.0"})
        playlist = sp.playlist_items(spotiplay[0])
        items = playlist['items']
        for song in items:
            song_name = song['track']['name']
            artists = song['track']['artists']
            name = ''
            for artist in artists:
                artist = artist['name']
                if len(name) == 0:
                    name += artist
                else:
                    name += f', {artist}'
            name += f' - {song_name}'
            _song = await _get_video_data(name, loop, ctx, ytdl)
            if not _song:
                items.pop(0)
                continue
            player = await get_player(ctx, True)
            await player.add_to_queue(_song)
            now_song = items[0]
            items.pop(0)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                loop.create_task(async_video_data(items, loop, ctx, ytdl, player))
            else:
                asyncio.run(async_video_data(items, loop, ctx, ytdl, player))
            if song == now_song and play:
                await player.play(ctx)
            break
        return []
    elif spotisong:
        ytdl = youtube_dl.YoutubeDL({"format": "bestaudio/best", "restrictfilenames": True, "noplaylist": True, "nocheckcertificate": True, "ignoreerrors": True, "logtostderr": False, "quiet": True, "no_warnings": True, "default_search": "auto", "source_address": "0.0.0.0"})
        song = sp.track(spotisong[0])
        song_name = song['name']
        artists = song['artists']
        name = ''
        for artist in artists:
            artist = artist['name']
            if len(name) == 0:
                name += artist
            else:
                name += artist
        name += f' - {song_name}'
        _song = await _get_video_data(name, loop, ctx, ytdl)
        if not _song:
            return None
        if play:
            player = await get_player(ctx, True)
            await player.add_to_queue(_song)
            await player.play(ctx)
        return _song
    elif ytplaylist:
        await ctx.send('Las playlist de youtube se demoran mas de lo normal dependiendo de la cantidad de canciones...')
        ytdl = youtube_dl.YoutubeDL({"format": "bestaudio/best", "restrictfilenames": True, "nocheckcertificate": True, "ignoreerrors": True, "logtostderr": False, "quiet": True, "no_warnings": True, "default_search": "auto", "source_address": "0.0.0.0"})
        song = await _get_video_data(ytplaylist[0], loop, ctx, ytdl)
        player = await get_player(ctx, True)
        if not song:
            return None
        await player.add_to_queue(song)
        if play:
            await player.play(ctx)
        return []
    else:
        ytdl = youtube_dl.YoutubeDL({"format": "bestaudio/best", "restrictfilenames": True, "noplaylist": True, "nocheckcertificate": True, "ignoreerrors": True, "logtostderr": False, "quiet": True, "no_warnings": True, "default_search": "auto", "source_address": "0.0.0.0"})
        song =  await _get_video_data(url, loop, ctx, ytdl)
        if not song:
            return None
        if play:
            player = await get_player(ctx, True)
            await player.add_to_queue(song)
            await player.play(ctx)
        return song

# Define Classes

class EmptyQueue(Exception):
    """Cannot skip because queue is empty"""
class NotPlaying(Exception):
    """Cannot <do something> because nothing is being played"""
class MusicPlayer(object):
    def __init__(self, ctx, queue):
        self.ctx = ctx
        self.voice = ctx.voice_client
        self.loop = ctx.bot.loop
        self._queue = queue
        if self.ctx.guild.id not in self._queue.keys():
            self._queue[self.ctx.guild.id] = []
        self.after_func = check_queue
        self.on_play_func = self.on_queue_func = self.on_skip_func = self.on_stop_func = self.on_pause_func = self.on_resume_func = self.on_loop_toggle_func = self.on_volume_change_func = self.on_remove_from_queue_func = None
        self.ffmpeg_opts = {"options": "-vn -loglevel quiet -hide_banner -nostats", "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0 -nostdin"}
    def on_queue(self, func):
        self.on_queue_func = func
    def on_play(self, func):
        self.on_play_func = func
    def on_skip(self, func):
        self.on_skip_func = func
    def on_stop(self, func):
        self.on_stop_func = func
    def on_pause(self, func):
        self.on_pause_func = func
    def on_resume(self, func):
        self.on_resume_func = func
    def on_loop_toggle(self, func):
        self.on_loop_toggle_func = func
    def on_volume_change(self, func):
        self.on_volume_change_func = func
    def on_remove_from_queue(self, func):
        self.on_remove_from_queue_func = func
    async def add_to_queue(self, song):
        self._queue[self.ctx.guild.id].append(song)
        if self.on_queue_func:
            await self.on_queue_func(self.ctx, song)
    async def queue(self, url, ctx, play=None):
        song = await get_video_data(url, self.loop, ctx, play)
        if type(song) is list:
            return []
        if not song:
            return None
        await self.add_to_queue(song)
        return song
    async def play(self, ctx, nowplaying=None):
        if nowplaying:
            song = self._queue[self.ctx.guild.id][0]
            music_now_song[ctx.guild.id] = song
            member = ctx.author

            yf = re.findall('https://www.youtube.com/watch.v=(\w.+)', song.url)
            yf = f'https://img.youtube.com/vi/{yf[0]}/mqdefault.jpg'

            prefix = await getPrefix(message=ctx)

            embed = discord.Embed(description=f'[{song.name}]({song.url})\nSi los botones no funcionan use `{prefix}nowplaying`', color=0xC81717)
            embed.set_footer(text=f'Pedida por: {song.order}')
            embed.set_author(name='Sonando ♪', icon_url=member.avatar_url)
            embed.set_thumbnail(url=yf)

            await buttons(ctx, embed)
        else:
            try:
                if music_random_playlist[ctx.guild.id]:
                    song = random.choice(self._queue[self.ctx.guild.id])
                else:
                    raise KeyError
            except KeyError:
                song = self._queue[self.ctx.guild.id][0]
            music_now_song[ctx.guild.id] = song
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.source, **self.ffmpeg_opts))
            self.voice.play(source, after=lambda error: self.after_func(self.ctx, self.ffmpeg_opts, self._queue, self.after_func, self.on_play_func, self.loop))
            if self.on_play_func:
                await self.on_play_func(self.ctx, song)

            member = ctx.author

            yf = re.findall('https://www.youtube.com/watch.v=(\w.+)', song.url)
            yf = f'https://img.youtube.com/vi/{yf[0]}/mqdefault.jpg'

            prefix = await getPrefix(message=ctx)

            embed = discord.Embed(description=f'[{song.name}]({song.url})\nSi los botones no funcionan use `{prefix}nowplaying`', color=0xC81717)
            embed.set_footer(text=f'Pedida por: {song.order}')
            embed.set_author(name='Sonando ♪', icon_url=member.avatar_url)
            embed.set_thumbnail(url=yf)

            await buttons(ctx, embed)
    async def skip_to(self, index):
        for x in range(index):
            if x == 0:
                self._queue[self.ctx.guild.id].remove(music_now_song[self.ctx.guild.id])
            else:
                self._queue[self.ctx.guild.id].pop(0)
        new = await self.skip()
        return new
    async def skip(self, force=False):
        if len(self._queue[self.ctx.guild.id]) == 0:
            raise NotPlaying
        elif not len(self._queue[self.ctx.guild.id]) > 1 and not force:
            raise EmptyQueue
        else:
            old = music_now_song[self.ctx.guild.id]
            old.is_looping = False if old.is_looping else False
            self.voice.stop()
            await asyncio.sleep(0.1)
            new = music_now_song[self.ctx.guild.id]
            if self.on_skip_func:
                await self.on_skip_func(self.ctx, old, new)
            return new
    async def pause(self):
        try:
            self.voice.pause()
            song = self._queue[self.ctx.guild.id][0]
        except:
            raise 'no hay ninguna cancion en reproduccion'
        if self.on_pause_func:
            await self.on_pause_func(self.ctx, song)
        return song
    async def resume(self):
        try:
            self.voice.resume()
            song = self._queue[self.ctx.guild.id][0]
        except:
            raise 'no hay ninguna cancion en reproduccion'
        if self.on_resume_func:
            await self.on_resume_func(self.ctx, song)
        return song
    def current_queue(self):
        try:
            return self._queue[self.ctx.guild.id]
        except KeyError:
            raise
    async def toggle_song_loop(self):
        try:
            song = self._queue[self.ctx.guild.id][0]
        except:
            raise
        if not song.is_looping:
            song.is_looping = True
        else:
            song.is_looping = False
        if self.on_loop_toggle_func:
            await self.on_loop_toggle_func(self.ctx, song)
        return song
    async def remove_from_queue(self, index):
        if index == 0:
            try:
                song = self._queue[self.ctx.guild.id][0]
            except:
                raise 'ninguna cancion en reproduccion'
            await self.skip(force=True)
            return song
        song = self._queue[self.ctx.guild.id][index]
        self._queue[self.ctx.guild.id].pop(index)
        if self.on_remove_from_queue_func:
            await self.on_remove_from_queue_func(self.ctx, song)
        return song
class Song(object):
    def __init__(self, source, url, title, description, views, duration, thumbnail, channel, channel_url, loop, order):
        self.source = source
        self.url = url
        self.title = title
        self.description = description
        self.views = views
        self.name = title
        self.duration = duration
        self.thumbnail = thumbnail
        self.channel = channel
        self.channel_url = channel_url
        self.is_looping = loop
        self.order = order


intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=getPrefix, intents=intents)
bot.remove_command('help')
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET')))
music_queue = {}
music_players = []
music_channels = {}
music_messages = []
music_random_playlist = {}
music_now_song = {}
voice_is_playing = {}


@tasks.loop(count=1)
async def music_delete_message(message):
    try:
        music_messages.remove(message)
    except:
        pass
    try:
        await message.edit(components=[])
    except:
        pass

@bot.event
async def on_ready():
    DiscordComponents(bot)
    async with aiosqlite.connect('main.db') as db:
        async with db.cursor() as cursor:
            await cursor.execute('CREATE TABLE IF NOT EXISTS bienvenidas (guild ID, channel ID)')
            await cursor.execute('CREATE TABLE IF NOT EXISTS level_system (guild ID, user ID, messages INT)')
            await cursor.execute('CREATE TABLE IF NOT EXISTS prefix_system (guild ID, prefix STR)')
        await db.commit()
    print(f'{bot.user} esta listo!')

@bot.event
async def on_message(message):
    if not message.author.bot:
        async with aiosqlite.connect('main.db') as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT messages FROM level_system WHERE guild = ? AND user = ?', (message.guild.id, message.author.id,))
                data = await cursor.fetchone()
                if data:
                    messages = data[0]
                    messages += 1
                    await cursor.execute('UPDATE level_system SET messages = ? WHERE user = ? AND guild = ?', (messages, message.author.id, message.guild.id,))
                else:
                    await cursor.execute('INSERT INTO level_system (guild, user, messages) VALUES (?, ?, ?)', (message.guild.id, message.author.id, 1,))
            await db.commit()
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    async with aiosqlite.connect('main.db') as db:
        async with db.cursor() as cursor:
            await cursor.execute('SELECT channel FROM bienvenidas WHERE guild = ?', (member.guild.id,))
            data = await cursor.fetchone()
            if data:
                channel = data[0]
                if channel == 0:
                    return
                channel = await bot.fetch_channel(channel)
                await channel.send(f'Bienvenido {member.mention} al servidor `{member.guild.name}`')
            else:
                return
        await db.commit()

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if before.channel and not after.channel and bot.voice_clients and not member.bot:
            for voice in bot.voice_clients:
                if before.channel == voice.channel:
                    members = voice.channel.members
                    for x in members:
                        if x.bot:
                            members.remove(x)
                    if len(members) == 0:
                        try:
                            del music_now_song[member.guild.id]
                        except:
                            pass
                        try:
                            channel, message = music_channels[member.guild.id]
                        except:
                            return
                        try:
                            del music_channels[member.guild.id]
                        except:
                            pass
                        channel = await bot.fetch_channel(channel)
                        await voice.disconnect()
                        await message.edit(components=[])
                        embed = discord.Embed(description='Agradeceria mucho que me recomendara a sus amigos :D', color=0xC81717)
                        embed.set_author(name='Desconectado')
                        embed.set_thumbnail(url=bot.user.avatar_url)
                        await channel.send(embed=embed)
                    break
        elif before.channel and not after.channel and member.bot and member.id == bot.user.id:
            try:
                del music_now_song[member.guild.id]
            except:
                pass
            try:
                channel, message = music_channels[member.guild.id]
                del music_channels[member.guild.id]
            except:
                return
            channel = await bot.fetch_channel(channel)
            await message.edit(components=[])
            embed = discord.Embed(description='Agradeceria mucho que me recomendara a sus amigos :D', color=0xC81717)
            embed.set_author(name='Desconectado')
            embed.set_thumbnail(url=bot.user.avatar_url)
            await channel.send(embed=embed)
    except Exception as e:
        print(f'Error en el evento \"on_voice_state_update\": {e}')

@bot.event
async def on_message_delete(message):
    if message.id in music_messages:
        try:
            music_messages.remove(message)
        except:
            pass

@bot.command(name='help')
async def help(ctx):

    prefix = await getPrefix(message=ctx)
    des = """
---SIMBOLOGIA COMANDOS---
> () = Texto obligatorio
> [] = Texto opcional

---ADMINISTRADORES---
> {0}Cbienvenida: Envia bienvenidas al canal de texto asignado

---MUSICA--
> {0}play (url/nombre de una cancion o playlist de youtube/spotify) [--random: Activa la reproduccion aleatoria]: Reproduce la cancion o playlist que hayas puesto
> {0}skip [numero]: Salta la cancion en reproduccion por la siguiente o la del numero que haya puesto
> {0}random: Activa la reproduccion aleatoria
> {0}loop: Activa la reproduccion en loop
> {0}stop: Para la musica y desconecta el bot

---LEVEL---
> {0}ranking: Top del server
> {0}level [mencion al usuario]: nivel del usuario

---PERSONALIZACION---
> {0}setprefix [prefix]: Cambia el prefix

---OTROS---
> {0}id [mencion al usuario]: id del usuario
""".format(prefix)

    embed = discord.Embed(description=des, color=0xC81717)
    embed.set_footer(text=f'Solicitado por {ctx.author}')
    embed.set_author(name=bot.user.name, icon_url=bot.user.avatar_url, url=os.getenv('BOT_INV'))

    await ctx.send(embed=embed)

@bot.command(name='level')
async def level(ctx, user=None):
    # Obtener datos del usuario
    if not user:
        member = ctx.author
        async with aiosqlite.connect('main.db') as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT messages FROM level_system WHERE guild = ? AND user = ?', (ctx.guild.id, member.id,))
                data = await cursor.fetchone()
                if data:
                    data = data[0]
                    xp = data
                    level = 0
                    while data >= 200:
                        data -= 200
                        level += 1
                    metxp = level + 1
                    metxp *= 200
                    percent = 100 * data / 200
                else:
                    return await ctx.send('ERROR: No se encuentra el usuario en la base de datos del servidor')
            await db.commit()
    else:
        user = re.findall('^<@!([0-9]+)>', user)
        if user:
            user_id = user[0]
            try:
                member = await ctx.guild.fetch_member(user_id)
            except:
                return await ctx.send('No se ha encontrado este usuario en el servidor')
            async with aiosqlite.connect('main.db') as db:
                async with db.cursor() as cursor:
                    await cursor.execute('SELECT messages FROM level_system WHERE guild = ? AND user = ?', (ctx.guild.id, member.id,))
                    data = await cursor.fetchone()
                    if data:
                        data = data[0]
                        xp = data
                        level = 0
                        while data >= 200:
                            data -= 200
                            level += 1
                        metxp = level + 1
                        metxp *= 200
                        percent = 100 * data / 200
                    else:
                        return await ctx.send('ERROR: No se encuentra el usuario en la base de datos del servidor')
                await db.commit()
        else:
            return await ctx.send('Asegurese de haber mencionado al usuario correctamente')
    
    # Crear imagen
    background = Editor('cogs/background.jpg')

    pfp = await load_image_async(str(member.avatar_url))
    pfp = Editor(pfp).resize((700, 700)).circle_image()
    poppins = Font(path='cogs/AmaticSC-Regular.ttf').poppins(size=110)

    background.paste(pfp.image, (120, 100))

    background.rectangle((130, 1070), width=2200, height=100, fill='white', radius=100)
    background.bar((130, 1070), max_width=2200, height=100, percentage=percent, fill='#F5238F', radius=100)
    background.text((870, 300), member.name + '#' + member.discriminator, font=poppins, color='white')

    background.rectangle((870, 430), width=1650, height=10, fill='#F5238F', radius=100)
    background.text((300, 924), 'Level: {:,d}'.format(level), font=poppins, color='white')
    background.text((900, 900), 'Messages: {:,d} / {:,d}'.format(xp, metxp), font=poppins, color='white')

    file = discord.File(fp=background.image_bytes, filename='tarjeta_xp.png')

    await ctx.send(file=file)

@bot.command(name='ranking')
async def ranking(ctx):
    async with aiosqlite.connect('main.db') as db:
        async with db.cursor() as cursor:
            await cursor.execute('SELECT user, messages FROM level_system WHERE guild = ?', (ctx.guild.id,))
            data = await cursor.fetchall()
            if data:
                data = sorted(data, key=lambda messages: messages[1], reverse=True)
                des = ''
                index = 0
                for x in data:
                    if index >= 50:
                        break
                    elif index == 0:
                        des += f'Top 1: <@{x[0]}>. Con {x[1]} mensajes! <:GamesPog:915374593588482099>\n\n'
                    elif index == 1:
                        des += f'Top 2: <@{x[0]}>. Con {x[1]} mensajes! <:BlobCatHeart:915374593471033394>\n\n'
                    elif index == 2:
                        des += f'Top 3: <@{x[0]}>. Con {x[1]} mensajes! <:amogusheart:915374593315840070>\n\n'
                    else:
                        top = index + 1
                        des += f'Top {top}: <@{x[0]}>. Con {x[1]} mensajes!\n\n'
                    index += 1
                embed = discord.Embed(title='Top', description=des, color=0xC81717)
                embed.set_footer(text=f'Solicitado por: {ctx.author}')
                embed.set_author(name=bot.user.name, icon_url=bot.user.avatar_url, url=os.getenv('BOT_INV'))
                await ctx.send(embed=embed)
            else:
                await ctx.send('ERROR: No se ha encontrado este servidor en la base de datos')
        await db.commit()

@bot.command(name='id')
async def id(ctx, user=None):
    if user:
        characters = '<@!>'
        for x in range(len(characters)):
            user = user.replace(characters[x], '')
        return await ctx.send(f'El id de <@{user}> es: {user}')
    await ctx.send(f'Tu id es: {ctx.author.id}')

@bot.command(name='Cbienvenida')
async def Cbienvenida(ctx):
    if not ctx.author.permissions_in(ctx.channel).manage_guild:
        return await ctx.send('Necesitas permisos de `Gestionar servidor`')
    text_channels = {}
    for guild in bot.guilds:
        if guild.id == ctx.guild.id:
            for channel in guild.channels:
                if type(channel) == discord.channel.TextChannel:
                    text_channels[channel.name] = channel.id
            break
    options = [SelectOption(label='No enviar bienvenidas', emoji='🚫', value=0)]
    for name, id in text_channels.items():
        options.append(SelectOption(label=name, value=id))
    message = await ctx.send('A que canal de texto quieres que se envien las bienvenidas?',
                    components=[
                        Select(placeholder='Selecciona el canal de texto!', options=options)
                    ]
                  )
    
    while True:
        interaction = await bot.wait_for('select_option')
        if interaction.author.id == ctx.author.id:
            value = int(interaction.values[0])
            async with aiosqlite.connect('main.db') as db:
                async with db.cursor() as cursor:
                    await cursor.execute('SELECT channel FROM bienvenidas WHERE guild = ?', (ctx.guild.id,))
                    data = await cursor.fetchone()
                    if data:
                        await cursor.execute('UPDATE bienvenidas SET channel = ? WHERE guild = ?', (value, ctx.guild.id,))
                    else:
                        await cursor.execute('INSERT INTO bienvenidas (guild, channel) VALUES (?, ?)', (ctx.guild.id, value,))
                await db.commit()
            await interaction.message.edit(components=[])
            if value == 0:
                await interaction.send('Bienvenidas canceladas!', ephemeral=False)
                break
            await interaction.send(f'Canal de texto <#{value}> seleccionado!', ephemeral=False)
            break
        await interaction.send('No puedes utilizar esta interaccion!')

@bot.command(name='setprefix')
async def setprefix(ctx, prefix=''):
    # Opcion para poner prefix si o si (prefix=None)
    """
    if not prefix:
        return await ctx.send('Debes poner un prefix')
    """
    
    async with aiosqlite.connect('main.db') as db:
        async with db.cursor() as cursor:
            await cursor.execute('SELECT prefix FROM prefix_system WHERE guild = ?', (ctx.guild.id,))
            data = await cursor.fetchone()
            if data:
                await cursor.execute('UPDATE prefix_system SET prefix = ? WHERE guild = ?', (prefix, ctx.guild.id,))
            else:
                await cursor.execute('INSERT INTO prefix_system (prefix, guild) VALUES (?, ?)', (prefix, ctx.guild.id,))
        await db.commit()
    
    if prefix == '':
        return await ctx.send('El prefix ha sido eliminado')
    await ctx.send(f'El prefix ha sido actualizado a: `{prefix}`')

@bot.command(name='play')
async def play(ctx, *args):
    try:
        if voice_is_playing[ctx.guild.id]:
            return await ctx.send('Hay una frase en reproduccion!')
    except:
        pass
    member = ctx.author
    before_connected = True
    if not member.voice:
        return await ctx.send('Primero debes estar en un canal de voz!')
    if ctx.voice_client:
        if ctx.voice_client.channel != member.voice.channel:
            return await ctx.send('Estoy ocupado en otro canal de voz!')
    if not ctx.voice_client:
        await member.voice.channel.connect()
        before_connected = False
    player = await get_player(ctx, before_connected)
    if not player:
        return
    url = ' '.join(args)
    if re.findall('(.+\w.+)--random', url):
        url = re.findall('(.+\w.+)--random', url)[0]
        characters = ' '
        url = ''.join( x for x in url if x not in characters)
        music_random_playlist[ctx.guild.id] = True
    if not ctx.voice_client.is_playing():
        song = await player.queue(url, ctx, True)
        if not song and type(song) != list:
            return await ctx.send('La cancion no ha sido agregada por ser calificada +18')
    else:
        song = await player.queue(url, ctx)
        if not song and type(song) != list:
            return await ctx.send('La cancion no ha sido agregada por ser calificada +18')
        if type(song) is list:
            embed = discord.Embed(description=f'Se ha añadido la playlist a la lista!', color=0xC81717)
            embed.set_footer(text=f'Añadida por: {song[0].order}')
            embed.set_author(name='Lista de reproduccion', icon_url=member.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f'La cancion `{song.name}` se añadio a la cola', color=0xC81717)
            embed.set_footer(text=f'Añadida por: {song.order}')
            embed.set_author(name='Lista de reproduccion', icon_url=member.avatar_url)
            await ctx.send(embed=embed)

@bot.command(name='stop')
async def stop(ctx):
    if not ctx.voice_client:
        return await ctx.send('No estoy en ningun canal de voz tonto')
    member = ctx.author
    if not member.voice or ctx.voice_client.channel != member.voice.channel:
        return await ctx.send('Debes estar en mi canal de voz')
    embed = discord.Embed(description='Agradeceria mucho que me recomendara a sus amigos :D', color=0xC81717)
    embed.set_author(name='Desconectado')
    embed.set_thumbnail(url=bot.user.avatar_url)
    await ctx.voice_client.disconnect()
    try:
        del music_channels[ctx.guild.id]
    except:
        pass
    return await ctx.send(embed=embed)

@bot.command(name='skip')
async def skip(ctx, index=1):
    try:
        if not ctx.voice_client:
            return await ctx.send('No estoy en ningun canal de voz tonto')
        member = ctx.author
        if not member.voice or ctx.voice_client.channel != member.voice.channel:
            return await ctx.send('Debes estar en mi canal de voz')
        if not ctx.voice_client.is_playing():
            return await ctx.send('No hay ninguna cancion en reproduccion!')
        index = int(index)
        player = await get_player(ctx, True)
        if index == 1:
            await player.skip()
        try:
            if music_random_playlist[ctx.guild.id]:
                return await ctx.send(f'No se puede skipear hasta la cancion numero {index} debido a que el modo random esta activo')
        except KeyError:
            pass
        if len(player.current_queue()) >= index:
            await player.skip_to(index)
        elif index != 1:
            await ctx.send('La lista es mas pequeña de lo que me pides :(')
    except Exception as e:
        print(f'Error en el comando \"skip\": {e}')

@bot.command(name='nowplaying')
async def nowplaying(ctx):
    try:
        if not ctx.voice_client:
            return await ctx.send('No estoy en ningun canal de voz tonto')
        member = ctx.author
        if not member.voice or ctx.voice_client.channel != member.voice.channel:
            return await ctx.send('Debes estar en mi canal de voz')
        if not ctx.voice_client.is_playing():
            return await ctx.send('No hay ninguna cancion en reproduccion!')
        player = await get_player(ctx, True)
        await player.play(ctx, True)
    except Exception as e:
        print(f'Error en el comando \"nowplaying\": {e}')

@bot.command(name='random')
async def random_playlist(ctx):
    try:
        if not ctx.voice_client:
            return await ctx.send('No estoy en ningun canal de voz tonto')
        member = ctx.author
        if not member.voice or ctx.voice_client.channel != member.voice.channel:
            return await ctx.send('Debes estar en mi canal de voz')
        if not ctx.voice_client.is_playing():
            return await ctx.send('No hay ninguna cancion en reproduccion!')
        player = await get_player(ctx, True)
        queue = player.current_queue()
        if len(queue) <= 1:
            return await ctx.send('La reproduccion random no se puede activar debido a que la lista de reproduccion es demasiado pequeña')
        try:
            if not music_random_playlist[ctx.guild.id]:
                music_random_playlist[ctx.guild.id] = True
                await ctx.send('La reproduccion random se ha activado!')
            else:
                raise KeyError
        except KeyError:
            music_random_playlist[ctx.guild.id] = False
            await ctx.send('La reproduccion random se ha desactivado!')
    except Exception as e:
        print(f'Error en el comando \"random\": {e}')

@bot.command(name='loop')
async def loop(ctx):
    try:
        if not ctx.voice_client:
            return await ctx.send('No estoy en ningun canal de voz tonto')
        member = ctx.author
        if not member.voice or ctx.voice_client.channel != member.voice.channel:
            return await ctx.send('Debes estar en mi canal de voz')
        if not ctx.voice_client.is_playing():
            return await ctx.send('No hay ninguna cancion en reproduccion!')
        player = await get_player(ctx, True)
        song = await player.toggle_song_loop()
        if not song.is_looping:
            await ctx.send(f'La cancion `{song.name}` ya no se reproducira en loop')
        else:
            await ctx.send(f'La cancion `{song.name}` se reproducira en loop')
    except Exception as e:
        print(f'Error en el comando \"loop\": {e}')

@bot.command(name='di')
async def di(ctx, *args):
    if not args:
        await ctx.send('Debes poner una frase para que yo la diga!')
    member = ctx.author
    if not member.voice:
        return await ctx.send('Primero debes estar en un canal de voz!')
    if ctx.voice_client:
        if ctx.voice_client.channel != member.voice.channel:
            return await ctx.send('Estoy ocupado en otro canal de voz!')
        try:
            music = music_now_song[ctx.guild.id]
        except:
            music = False
        if ctx.voice_client.is_playing() and music:
            return await ctx.send('Hay musica en reproduccion!')
    if not ctx.voice_client:
        await member.voice.channel.connect()
    text = ' '.join(args)
    speech = gTTS(text=text, lang='pt')
    output_file = f'./cogs/{ctx.author.id}.mp3'
    speech.save(output_file)
    voice_file = eyed3.load(output_file)
    secs = int(voice_file.info.time_secs)
    if secs >= 59:
        os.remove(output_file)
        return await ctx.send('El texto es muy largo!')
    try:
        music = music_now_song[ctx.guild.id]
    except:
        music = False
    try:
        voice = voice_is_playing[ctx.guild.id]
    except:
        voice = False
    while voice and music:
        try:
            music = music_now_song[ctx.guild.id]
        except:
            music = False
        try:
            voice = voice_is_playing[ctx.guild.id]
        except:
            voice = False
    if not music and not voice:
        voice_is_playing[ctx.guild.id] = True
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=output_file))
        await asyncio.sleep(1)
        while True:
            try:
                os.remove(output_file)
                break
            except PermissionError:
                pass
        voice_is_playing[ctx.guild.id] = False

@bot.command(name='servers')
async def serversCREATOR(ctx):
    if ctx.author.id != 417513296376233986:
        return
    guilds = ''
    for guild in bot.guilds:
        guilds += f'{guild.name}\n'
    await ctx.send(guilds)


bot.run(os.getenv('DISCORD_TOKEN'))
