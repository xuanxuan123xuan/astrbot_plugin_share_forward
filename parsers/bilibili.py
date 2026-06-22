"""B 站解析器：b23.tv / bilibili.com
完全匿名可调，最稳。
"""
from __future__ import annotations

import re
from typing import Optional

from .base import BaseParser, ParsedItem, ParseError


_RE_BILIBILI = re.compile(
    r"(?:https?://)?(?:"
    r"b23\.tv/[A-Za-z0-9]+|"
    r"(?:www\.|m\.)?bilibili\.com/video/[A-Za-z0-9]+|"
    r"(?:www\.|m\.)?bilibili\.com/[a-zA-Z0-9?=&_/.\-]+"
    r")",
    re.IGNORECASE,
)
_RE_BV = re.compile(r"(BV[0-9A-Za-z]{10})")
_RE_AV = re.compile(r"av(\d+)", re.IGNORECASE)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com",
}


class BilibiliParser(BaseParser):
    platform = "bilibili"

    async def can_parse(self, url: str) -> bool:
        return bool(_RE_BILIBILI.search(url))

    async def parse(self, url: str) -> ParsedItem:
        m = _RE_BILIBILI.search(url)
        if not m:
            raise ParseError("not bilibili")
        page_url = m.group(0)
        if not page_url.startswith("http"):
            page_url = "https://" + page_url

        # 1. 短链跟随
        bv = _extract_bv(page_url)
        aid: Optional[int] = None
        if not bv:
            # b23.tv 等需要跟随
            try:
                resp = await self.http.get(
                    page_url, headers=_HEADERS, follow_redirects=True
                )
                final_url = str(resp.url)
            except Exception as e:  # noqa: BLE001
                raise ParseError(f"短链跳转失败: {e}") from e
            bv = _extract_bv(final_url)
            if not bv:
                m_av = _RE_AV.search(final_url)
                if m_av:
                    aid = int(m_av.group(1))

        if not bv and not aid:
            raise ParseError("未能从链接中提取 BV/AV 号")

        # 2. 视频详情
        params = {"bvid": bv} if bv else {"aid": aid}
        try:
            r = await self.http.get(
                "https://api.bilibili.com/x/web-interface/view",
                params=params,
                headers=_HEADERS,
            )
            data = r.json()
        except Exception as e:  # noqa: BLE001
            raise ParseError(f"调用 view 接口失败: {e}") from e

        if data.get("code") != 0:
            raise ParseError(f"view 接口返回错误: {data.get('message')}")
        info = data["data"]

        item = ParsedItem(
            platform="bilibili",
            raw_url=url,
            item_type="video",
            title=info.get("title", ""),
            author=(info.get("owner") or {}).get("name", ""),
            desc=info.get("desc", ""),
            cover=info.get("pic", ""),
            canonical_url=f"https://www.bilibili.com/video/{info.get('bvid', bv)}",
            extra={
                "bvid": info.get("bvid", bv or ""),
                "aid": str(info.get("aid", aid or "")),
                "duration": str(info.get("duration", "")),
                "view": str((info.get("stat") or {}).get("view", "")),
            },
        )

        # 3. 原视频流地址。优先 durl（通常音视频合一），失败再兜底 dash.video。
        try:
            video_url = await self._fetch_play_url(info)
            if video_url:
                item.video_url = video_url
                item.video_referer = item.canonical_url or "https://www.bilibili.com/"
        except Exception as e:  # noqa: BLE001
            self.logger.debug(f"[bilibili] 视频流拉取失败: {e}")

        # 4. 评论 Top 3
        if self.config.get("include_top_comments", True):
            try:
                aid_for_reply = info.get("aid") or aid
                if aid_for_reply:
                    rc = await self.http.get(
                        "https://api.bilibili.com/x/v2/reply/main",
                        params={
                            "type": 1,
                            "oid": aid_for_reply,
                            "mode": 3,  # 按热度
                            "next": 0,
                        },
                        headers=_HEADERS,
                    )
                    rj = rc.json()
                    if rj.get("code") == 0:
                        replies = (rj.get("data") or {}).get("replies") or []
                        for rep in replies[:3]:
                            item.comments.append({
                                "user": (rep.get("member") or {}).get("uname", ""),
                                "content": (rep.get("content") or {}).get("message", ""),
                                "like": str(rep.get("like", 0)),
                            })
            except Exception as e:  # noqa: BLE001
                self.logger.debug(f"[bilibili] 评论拉取失败: {e}")

        return item

    async def _fetch_play_url(self, info: dict) -> str:
        bvid = info.get("bvid")
        cid = info.get("cid")
        if not bvid or not cid:
            return ""

        # html5 + fnval=0 更容易返回 durl，适合 QQ 作为普通视频文件发送。
        params = {
            "bvid": bvid,
            "cid": cid,
            "qn": 64,
            "fnval": 0,
            "fourk": 0,
            "otype": "json",
            "platform": "html5",
            "high_quality": 1,
        }
        r = await self.http.get(
            "https://api.bilibili.com/x/player/playurl",
            params=params,
            headers=_HEADERS,
        )
        data = r.json()
        if data.get("code") == 0:
            play = data.get("data") or {}
            durl = play.get("durl") or []
            if durl:
                return durl[0].get("url", "")

        # 兜底：DASH 可能是音视频分离，这里只取视频流，至少保证“原视频”能出现。
        dash_params = dict(params)
        dash_params["fnval"] = 16
        r2 = await self.http.get(
            "https://api.bilibili.com/x/player/playurl",
            params=dash_params,
            headers=_HEADERS,
        )
        data2 = r2.json()
        if data2.get("code") != 0:
            return ""
        dash = ((data2.get("data") or {}).get("dash") or {})
        videos = dash.get("video") or []
        if not videos:
            return ""
        videos.sort(key=lambda x: int(x.get("bandwidth", 0) or 0), reverse=True)
        best = videos[0]
        return best.get("base_url") or best.get("baseUrl") or ""


def _extract_bv(url: str) -> Optional[str]:
    m = _RE_BV.search(url)
    return m.group(1) if m else None
