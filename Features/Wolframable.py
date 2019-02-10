import re
import urllib.parse

import requests
from lxml import etree

from Features.AbstractFeature import AbstractFeature
from preferences import prefs_singleton


class Wolframable(AbstractFeature):
    # security
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    api_url = 'https://api.wolframalpha.com/v2/query'
    query_url = 'https://www.wolframalpha.com/input/?i={}'
    show_pods = {'Input': True, 'Result': True, 'UnitConversion': True, 'AdditionalConversion': True}

    def __init__(self):
        self.api_key = self._try_read_key()

    async def message_filter(self, bot, source, target, message, highlighted):
        if not ((message.startswith('wolfram') and highlighted) or message.startswith('!wolfram')):
            return False
        if not self.api_key:
            await bot.message(source, 'API key not found!')
            return True
        input_query = message[message.index('wolfram ') + 8:].strip()
        params = {
            'input': input_query,
            'format': 'plaintext',
            'appid': self.api_key
        }

        request = requests.get(Wolframable.api_url, params=params)
        url = Wolframable.query_url.format(urllib.parse.quote_plus(input_query))
        try:
            request.raise_for_status()
        except requests.HTTPError as e:
            await bot.message(source, f'Error getting query: {e.response.status_code}')
            raise

        if request.status_code != requests.codes.ok:
            await bot.message(source, f'Wolfram error: {request.status_code} | {url}')
            return True
        result = etree.fromstring(request.content, parser=Wolframable.parser)

        pod_texts = {}
        pods = result.xpath('//pod')
        important_pods = [pod for pod in pods if 'primary' in pod.attrib.keys() or Wolframable.show_pods.get(pod.attrib['id'], False)]
        for pod in important_pods:
            pod_id = pod.attrib['id']
            title = pod.attrib['title']

            results = []
            # Format subpods
            for subpod in pod.xpath('subpod'):
                podinfo = f'{subpod.attrib["title"]} ' if subpod.attrib['title'] else ''

                pod_results = []
                for subinfo in subpod.xpath('plaintext/text()'):
                    # Itemize units (separate lines)
                    values = []
                    for item in subinfo.split('\n'):
                        # Format 'key | value'
                        item = re.sub(r'^([\w\s]+)\s+\|\s+', '\\1: ', item)
                        # Replace inner '|' (eg weather forecast)
                        item = re.sub(r'(\))\s+\|\s+', '\\1 - ', item)
                        # Colorize '(extra info)', preceded with whitespace
                        item = re.sub(r'\s+(\([^()]+\))', '\\1 ', item)
                        # Remove extra spaces
                        item = re.sub(r'\s{2,}', ' ', item)
                        # Add
                        values.append(item.strip())
                    # Put 'em back together
                    subinfo = ' | '.join(values)
                    if subinfo:
                        pod_results.append(subinfo)

                podinfo += ''.join(pod_results)
                results.append(podinfo)

            if results:
                info = ' | '.join(results)
                if pod_id == 'Input':
                    # Strip verbose 'Input interp/info'
                    title = title.replace(' interpretation', '').replace(' information', '')
                    # Strip open/closing parentheses around input
                if pod_id in ['AdditionalConversion', 'UnitConversion']:
                    # Reduce verbosity (just print 'Conversions')
                    title = 'C' + title[title.index('conv') + 1:]
                title += ': '
                pod_texts[pod_id] = title + info

        # NOTHING??
        if not pod_texts:
            await bot.message(source, 'Nothing found! | ' + url)
            return True

        # Sometimes input will be the only pod from filtering
        if 'Input' in pod_texts and len(pod_texts) == 1:
            await bot.message(source, 'Extra info filtered | ' + url)

        # Append input to result
        if 'Input' in pod_texts and 'Result' in pod_texts:
            pod_texts['Result'] = f'{pod_texts["Result"]} | {pod_texts["Input"]}'
            del pod_texts['Input']

        # Print result/input first
        if 'Input' in pod_texts:
            await bot.message(source, pod_texts['Input'])
            del pod_texts['Input']
        if 'Result' in pod_texts:
            await bot.message(source, pod_texts['Result'])
            del pod_texts['Result']

        # Print remaining info
        for key in pod_texts:
            await bot.message(source, pod_texts[key])
        return True

    def _try_read_key(self):
        api_key = prefs_singleton.read_value(type(self).__name__ + '_wolfram_api_key')
        if not api_key:
            prefs_singleton.write_value(type(self).__name__ + '_wolfram_api_key', '')
        return api_key

    @staticmethod
    def description():
        return 'Computes a given input using Wolfram Alpha.  Usage: "!wolfram <input>"'
