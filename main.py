#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
联系人提醒系统 - Kivy 手机版
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

from contact_manager import ContactManager

# 配色
COLORS = {
    'primary': '#4a90d9',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'success': '#27ae60',
    'bg': '#f0f4f8',
    'white': '#ffffff',
    'text': '#2c3e50',
    'gray': '#888888',
}


def hex_color(s, alpha=1):
    """十六进制颜色转RGBA"""
    c = get_color_from_hex(s)
    return (c[0], c[1], c[2], alpha)


class TodayScreen(Screen):
    """今日提醒页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        layout.canvas.before.clear()
        with layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*hex_color(COLORS['bg']))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_rect, pos=self._update_rect)

        # 标题
        title = Label(
            text='📅 今日提醒',
            font_size=sp(22),
            bold=True,
            size_hint=(1, None),
            height=dp(40),
            color=hex_color(COLORS['text'])
        )
        layout.add_widget(title)

        # 日期
        from datetime import datetime
        date_label = Label(
            text=datetime.now().strftime('%Y-%m-%d'),
            font_size=sp(13),
            size_hint=(1, None),
            height=dp(25),
            color=hex_color(COLORS['gray'])
        )
        layout.add_widget(date_label)

        # 统计卡片
        self.stats_box = BoxLayout(size_hint=(1, None), height=dp(70), spacing=dp(5))
        layout.add_widget(self.stats_box)

        # 内容滚动区
        self.scroll = ScrollView()
        self.content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(6),
            padding=(0, dp(5))
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        layout.add_widget(self.scroll)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def refresh(self):
        """刷新页面"""
        app = App.get_running_app()
        mgr = app.manager

        # 统计卡片
        self.stats_box.clear_widgets()
        stats = mgr.get_statistics()
        for label, value, color in [
            ('总联系人', stats['total'], 'primary'),
            ('已逾期', stats['overdue'], 'danger'),
            ('今日需联系', stats['today_due'], 'warning'),
        ]:
            card = self._make_stat_card(label, value, color)
            self.stats_box.add_widget(card)

        # 联系人列表
        self.content.clear_widgets()
        need_contact, overdue = mgr.get_today_contacts()

        if overdue:
            self.content.add_widget(self._make_section_title(
                f'🔴 已逾期需要立即联系（{len(overdue)}人）', 'danger'))
            for c in overdue:
                self.content.add_widget(self._make_contact_card(c, 'overdue', mgr))

        if need_contact:
            # 全部标记按钮
            btn_all = Button(
                text='✅ 全部标记已联系',
                size_hint=(1, None),
                height=dp(45),
                background_color=hex_color(COLORS['primary']),
                background_normal='',
                font_size=sp(15)
            )
            btn_all.bind(on_release=lambda x: self.mark_all())
            self.content.add_widget(btn_all)

            self.content.add_widget(self._make_section_title(
                f'🟡 今天需要联系（{len(need_contact)}人）', 'warning'))
            for c in need_contact:
                self.content.add_widget(self._make_contact_card(c, 'today', mgr))

        if not overdue and not need_contact:
            if stats['total'] == 0:
                self.content.add_widget(Label(
                    text='还没有联系人\n请点击下方「联系人」添加或导入',
                    size_hint=(1, None), height=dp(150),
                    halign='center', font_size=sp(15),
                    color=hex_color(COLORS['gray'])
                ))
            else:
                self.content.add_widget(Label(
                    text='✅ 今天没有需要联系的人\n继续保持！',
                    size_hint=(1, None), height=dp(150),
                    halign='center', font_size=sp(16),
                    color=hex_color(COLORS['success'])
                ))

    def _make_stat_card(self, label, value, color):
        """创建统计卡片"""
        card = BoxLayout(orientation='vertical', padding=dp(5))
        from kivy.graphics import Color, Rectangle, Line
        with card.canvas.before:
            Color(*hex_color(COLORS['white']))
            card_bg = Rectangle(pos=card.pos, size=card.size)
            Color(*hex_color(COLORS[color]))
            card_line = Line(rectangle=(card.x, card.y, card.width, card.height), width=1.2)

        def update_bg(instance, value):
            card_bg.pos = instance.pos
            card_bg.size = instance.size
            card_line.rectangle = (instance.x, instance.y, instance.width, instance.height)
        card.bind(pos=update_bg, size=update_bg)

        value_label = Label(
            text=str(value),
            font_size=sp(20),
            bold=True,
            color=hex_color(COLORS[color])
        )
        label_widget = Label(
            text=label,
            font_size=sp(11),
            color=hex_color(COLORS['gray'])
        )
        card.add_widget(value_label)
        card.add_widget(label_widget)
        return card

    def _make_section_title(self, text, color):
        """创建区块标题"""
        return Label(
            text=text,
            size_hint=(1, None),
            height=dp(35),
            font_size=sp(15),
            bold=True,
            color=hex_color(COLORS[color]),
            halign='left',
            valign='middle',
            text_size=(Window.width - dp(40), None)
        )

    def _make_contact_card(self, contact, status, mgr):
        """创建联系人卡片"""
        card = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(75),
            padding=dp(8),
            spacing=dp(8)
        )

        from kivy.graphics import Color, Rectangle
        with card.canvas.before:
            Color(*hex_color(COLORS['white']))
            bg = Rectangle(pos=card.pos, size=card.size)
            Color(*hex_color(COLORS['danger' if status == 'overdue' else 'warning']))
            bar = Rectangle(pos=(card.x, card.y), size=(dp(4), card.height))

        def update_bg(instance, value):
            bg.pos = instance.pos
            bg.size = instance.size
            bar.pos = (instance.x, instance.y)
            bar.size = (dp(4), instance.height)
        card.bind(pos=update_bg, size=update_bg)

        # 信息区
        info_box = BoxLayout(orientation='vertical', size_hint=(1, 1))
        name_text = contact['name']
        if contact.get('phone'):
            name_text += f"  📱{contact['phone']}"
        name_label = Label(
            text=name_text,
            font_size=sp(15),
            bold=True,
            halign='left',
            valign='middle',
            size_hint=(1, 0.5),
            color=hex_color(COLORS['text'])
        )
        name_label.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))

        if status == 'overdue':
            days = mgr.get_overdue_days(contact)
            meta_text = f"逾期 {days} 天 · 上次 {contact['last_contact']}"
            meta_color = COLORS['danger']
        else:
            meta_text = f"上次 {contact['last_contact']} · 间隔 {contact['interval']} 天"
            meta_color = COLORS['gray']

        meta_label = Label(
            text=meta_text,
            font_size=sp(12),
            halign='left',
            valign='middle',
            size_hint=(1, 0.5),
            color=hex_color(meta_color)
        )
        meta_label.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))

        info_box.add_widget(name_label)
        info_box.add_widget(meta_label)

        # 标记按钮
        btn = Button(
            text='✅',
            size_hint=(None, 1),
            width=dp(50),
            font_size=sp(18),
            background_color=hex_color(COLORS['success']),
            background_normal=''
        )
        btn.bind(on_release=lambda x, cid=contact['id']: self.mark_one(cid))

        card.add_widget(info_box)
        card.add_widget(btn)
        return card

    def mark_one(self, contact_id):
        """标记单个已联系"""
        app = App.get_running_app()
        app.manager.mark_contacted(contact_id)
        app.show_toast('已标记为已联系')
        self.refresh()

    def mark_all(self):
        """全部标记已联系"""
        app = App.get_running_app()
        need_contact, _ = app.manager.get_today_contacts()
        for c in need_contact:
            app.manager.mark_contacted(c['id'])
        app.show_toast(f'已标记 {len(need_contact)} 人')
        self.refresh()


class ContactsScreen(Screen):
    """联系人列表页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        from kivy.graphics import Color, Rectangle
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        with layout.canvas.before:
            Color(*hex_color(COLORS['bg']))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_rect, pos=self._update_rect)

        # 标题 + 操作按钮
        header = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(5))
        title = Label(
            text='👥 联系人',
            font_size=sp(20), bold=True,
            halign='left', valign='middle',
            color=hex_color(COLORS['text'])
        )
        title.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        header.add_widget(title)
        layout.add_widget(header)

        # 操作按钮行
        btn_row = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(5))

        btn_add = Button(
            text='➕ 添加', font_size=sp(13),
            background_color=hex_color(COLORS['primary']),
            background_normal=''
        )
        btn_add.bind(on_release=lambda x: self.go_add())

        btn_export = Button(
            text='📤 导出', font_size=sp(13),
            background_color=hex_color(COLORS['success']),
            background_normal=''
        )
        btn_export.bind(on_release=lambda x: self.export_data())

        btn_row.add_widget(btn_add)
        btn_row.add_widget(btn_export)
        layout.add_widget(btn_row)

        # 搜索框
        self.search_input = TextInput(
            hint_text='🔍 搜索姓名、手机号、备注',
            size_hint=(1, None),
            height=dp(42),
            multiline=False,
            font_size=sp(14),
            background_color=hex_color(COLORS['white'])
        )
        self.search_input.bind(text=lambda x, v: self.refresh())
        layout.add_widget(self.search_input)

        # 列表
        self.scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(6),
            padding=(0, dp(5))
        )
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        layout.add_widget(self.scroll)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def go_add(self):
        App.get_running_app().sm.current = 'add'

    def export_data(self):
        """导出数据到可访问目录"""
        app = App.get_running_app()
        try:
            filepath = app.export_to_shared()
            app.show_toast(f'已导出到: {filepath}')
        except Exception as e:
            app.show_toast(f'导出失败: {e}')

    def refresh(self):
        """刷新列表"""
        self.list_box.clear_widgets()
        app = App.get_running_app()
        mgr = app.manager

        keyword = self.search_input.text.strip()
        contacts = mgr.search_contacts(keyword)

        if not contacts:
            self.list_box.add_widget(Label(
                text='暂无联系人' if not keyword else '没有找到匹配的联系人',
                size_hint=(1, None), height=dp(120),
                halign='center', font_size=sp(14),
                color=hex_color(COLORS['gray'])
            ))
            return

        # 按状态排序
        order = {'overdue': 0, 'today': 1, 'upcoming': 2, 'normal': 3}
        contacts.sort(key=lambda c: (order[mgr.get_contact_status(c)], c['name']))

        for c in contacts:
            self.list_box.add_widget(self._make_card(c, mgr))

    def _make_card(self, contact, mgr):
        """创建联系人卡片"""
        status = mgr.get_contact_status(contact)
        next_date = mgr.get_next_contact_date(contact)

        card = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(80),
            padding=dp(8),
            spacing=dp(6)
        )

        from kivy.graphics import Color, Rectangle
        with card.canvas.before:
            Color(*hex_color(COLORS['white']))
            bg = Rectangle(pos=card.pos, size=card.size)
            status_color = {
                'overdue': COLORS['danger'],
                'today': COLORS['warning'],
                'upcoming': COLORS['success'],
                'normal': '#dddddd'
            }[status]
            Color(*hex_color(status_color))
            bar = Rectangle(pos=(card.x, card.y), size=(dp(4), card.height))

        def update_bg(instance, value):
            bg.pos = instance.pos
            bg.size = instance.size
            bar.pos = (instance.x, instance.y)
            bar.size = (dp(4), instance.height)
        card.bind(pos=update_bg, size=update_bg)

        # 信息区
        info = BoxLayout(orientation='vertical', size_hint=(1, 1))

        name_label = Label(
            text=contact['name'],
            font_size=sp(15), bold=True,
            halign='left', valign='middle',
            size_hint=(1, 0.4),
            color=hex_color(COLORS['text'])
        )
        name_label.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))

        meta = f"间隔{contact['interval']}天 · 下次{next_date}"
        if contact.get('phone'):
            meta = f"📱{contact['phone']} · " + meta

        meta_label = Label(
            text=meta,
            font_size=sp(11),
            halign='left', valign='middle',
            size_hint=(1, 0.3),
            color=hex_color(COLORS['gray'])
        )
        meta_label.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))

        info.add_widget(name_label)
        info.add_widget(meta_label)

        if contact.get('remark'):
            remark_label = Label(
                text=f"📝 {contact['remark']}",
                font_size=sp(11),
                halign='left', valign='middle',
                size_hint=(1, 0.3),
                color=hex_color(COLORS['gray'])
            )
            remark_label.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
            info.add_widget(remark_label)

        # 操作按钮
        btns = BoxLayout(orientation='vertical', size_hint=(None, 1), width=dp(45), spacing=dp(2))

        btn_edit = Button(
            text='✏️', font_size=sp(14),
            background_color=hex_color(COLORS['primary']),
            background_normal=''
        )
        btn_edit.bind(on_release=lambda x, c=contact: self.edit(c))

        btn_del = Button(
            text='🗑️', font_size=sp(14),
            background_color=hex_color(COLORS['danger']),
            background_normal=''
        )
        btn_del.bind(on_release=lambda x, c=contact: self.delete(c))

        btns.add_widget(btn_edit)
        btns.add_widget(btn_del)

        card.add_widget(info)
        card.add_widget(btns)
        return card

    def edit(self, contact):
        """跳转到编辑页"""
        app = App.get_running_app()
        app.edit_screen.load_contact(contact)
        app.sm.current = 'edit'

    def delete(self, contact):
        """删除联系人"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(
            text=f"确定删除「{contact['name']}」吗？",
            font_size=sp(15)
        ))
        btns = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))

        popup = Popup(
            title='确认删除',
            content=content,
            size_hint=(0.85, 0.3),
            title_size=sp(16)
        )

        def do_delete(instance):
            app = App.get_running_app()
            app.manager.delete_contact(contact['id'])
            popup.dismiss()
            self.refresh()
            app.show_toast('已删除')

        btn_yes = Button(
            text='删除', background_color=hex_color(COLORS['danger']),
            background_normal=''
        )
        btn_yes.bind(on_release=do_delete)

        btn_no = Button(text='取消', background_normal='')
        btn_no.bind(on_release=popup.dismiss)

        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        content.add_widget(btns)

        popup.open()


class AddScreen(Screen):
    """添加联系人页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        from kivy.graphics import Color, Rectangle
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with layout.canvas.before:
            Color(*hex_color(COLORS['bg']))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_rect, pos=self._update_rect)

        title = Label(
            text='➕ 添加联系人',
            font_size=sp(20), bold=True,
            size_hint=(1, None), height=dp(45),
            color=hex_color(COLORS['text'])
        )
        layout.add_widget(title)

        # 表单
        form = BoxLayout(orientation='vertical', spacing=dp(10), size_hint=(1, None), height=dp(320))
        form.canvas.before.clear()

        self.name_input = self._make_input('姓名 *', form)
        self.phone_input = self._make_input('手机号（选填）', form, input_type='number')

        # 间隔选择
        form.add_widget(Label(
            text='联系间隔（天）', font_size=sp(13),
            size_hint=(1, None), height=dp(22),
            halign='left', color=hex_color(COLORS['text'])
        ))
        self.interval_spinner = Spinner(
            text='7',
            values=['1', '2', '3', '5', '7', '10', '14', '21', '30', '60', '90'],
            size_hint=(1, None),
            height=dp(42),
            font_size=sp(15),
            background_color=hex_color(COLORS['white'])
        )
        form.add_widget(self.interval_spinner)

        self.remark_input = self._make_input('备注（选填）', form)

        layout.add_widget(form)

        # 按钮
        btns = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))

        btn_save = Button(
            text='✅ 保存', font_size=sp(15),
            background_color=hex_color(COLORS['primary']),
            background_normal=''
        )
        btn_save.bind(on_release=lambda x: self.save())

        btn_cancel = Button(
            text='取消', font_size=sp(15),
            background_normal=''
        )
        btn_cancel.bind(on_release=lambda x: self.cancel())

        btns.add_widget(btn_save)
        btns.add_widget(btn_cancel)
        layout.add_widget(btns)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _make_input(self, hint, parent, input_type='text'):
        """创建输入框"""
        parent.add_widget(Label(
            text=hint, font_size=sp(13),
            size_hint=(1, None), height=dp(22),
            halign='left', color=hex_color(COLORS['text'])
        ))
        inp = TextInput(
            hint_text=hint,
            size_hint=(1, None), height=dp(42),
            multiline=False,
            font_size=sp(15),
            input_type=input_type,
            background_color=hex_color(COLORS['white'])
        )
        parent.add_widget(inp)
        return inp

    def save(self):
        """保存联系人"""
        app = App.get_running_app()
        name = self.name_input.text.strip()

        if not name:
            app.show_toast('请输入姓名')
            return

        try:
            interval = int(self.interval_spinner.text)
            if interval <= 0:
                raise ValueError
        except ValueError:
            app.show_toast('联系间隔必须是正整数')
            return

        phone = self.phone_input.text.strip()
        remark = self.remark_input.text.strip()

        ok, msg = app.manager.add_contact(name, interval, phone, remark)
        if ok:
            app.show_toast('添加成功')
            self.clear_form()
            app.contacts_screen.refresh()
            app.sm.current = 'contacts'
        else:
            app.show_toast(msg)

    def cancel(self):
        """取消，返回"""
        App.get_running_app().sm.current = 'contacts'

    def clear_form(self):
        """清空表单"""
        self.name_input.text = ''
        self.phone_input.text = ''
        self.remark_input.text = ''
        self.interval_spinner.text = '7'


class EditScreen(Screen):
    """编辑联系人页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_contact = None
        self.build_ui()

    def build_ui(self):
        from kivy.graphics import Color, Rectangle
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with layout.canvas.before:
            Color(*hex_color(COLORS['bg']))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_rect, pos=self._update_rect)

        title = Label(
            text='✏️ 编辑联系人',
            font_size=sp(20), bold=True,
            size_hint=(1, None), height=dp(45),
            color=hex_color(COLORS['text'])
        )
        layout.add_widget(title)

        # 姓名（只读显示）
        self.name_label = Label(
            text='', font_size=sp(15), bold=True,
            size_hint=(1, None), height=dp(35),
            color=hex_color(COLORS['primary'])
        )
        layout.add_widget(self.name_label)

        form = BoxLayout(orientation='vertical', spacing=dp(10), size_hint=(1, None), height=dp(280))

        # 手机号
        form.add_widget(Label(
            text='手机号', font_size=sp(13),
            size_hint=(1, None), height=dp(22),
            halign='left', color=hex_color(COLORS['text'])
        ))
        self.phone_input = TextInput(
            size_hint=(1, None), height=dp(42),
            multiline=False, font_size=sp(15),
            input_type='number',
            background_color=hex_color(COLORS['white'])
        )
        form.add_widget(self.phone_input)

        # 间隔
        form.add_widget(Label(
            text='联系间隔（天）', font_size=sp(13),
            size_hint=(1, None), height=dp(22),
            halign='left', color=hex_color(COLORS['text'])
        ))
        self.interval_spinner = Spinner(
            text='7',
            values=['1', '2', '3', '5', '7', '10', '14', '21', '30', '60', '90'],
            size_hint=(1, None), height=dp(42),
            font_size=sp(15),
            background_color=hex_color(COLORS['white'])
        )
        form.add_widget(self.interval_spinner)

        # 备注
        form.add_widget(Label(
            text='备注', font_size=sp(13),
            size_hint=(1, None), height=dp(22),
            halign='left', color=hex_color(COLORS['text'])
        ))
        self.remark_input = TextInput(
            size_hint=(1, None), height=dp(42),
            multiline=False, font_size=sp(15),
            background_color=hex_color(COLORS['white'])
        )
        form.add_widget(self.remark_input)

        layout.add_widget(form)

        btns = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))

        btn_save = Button(
            text='💾 保存', font_size=sp(15),
            background_color=hex_color(COLORS['primary']),
            background_normal=''
        )
        btn_save.bind(on_release=lambda x: self.save())

        btn_cancel = Button(
            text='取消', font_size=sp(15),
            background_normal=''
        )
        btn_cancel.bind(on_release=lambda x: self.cancel())

        btns.add_widget(btn_save)
        btns.add_widget(btn_cancel)
        layout.add_widget(btns)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def load_contact(self, contact):
        """加载联系人数据"""
        self.current_contact = contact
        self.name_label.text = contact['name']
        self.phone_input.text = contact.get('phone', '')
        self.interval_spinner.text = str(contact['interval'])
        self.remark_input.text = contact.get('remark', '')

    def save(self):
        """保存修改"""
        if not self.current_contact:
            return

        app = App.get_running_app()
        try:
            interval = int(self.interval_spinner.text)
            if interval <= 0:
                raise ValueError
        except ValueError:
            app.show_toast('联系间隔必须是正整数')
            return

        ok, msg = app.manager.update_contact(
            self.current_contact['id'],
            phone=self.phone_input.text.strip(),
            interval=interval,
            remark=self.remark_input.text.strip()
        )
        if ok:
            app.show_toast('修改成功')
            app.contacts_screen.refresh()
            app.sm.current = 'contacts'
        else:
            app.show_toast(msg)

    def cancel(self):
        App.get_running_app().sm.current = 'contacts'


class StatsScreen(Screen):
    """统计页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        from kivy.graphics import Color, Rectangle
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        with layout.canvas.before:
            Color(*hex_color(COLORS['bg']))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_rect, pos=self._update_rect)

        title = Label(
            text='📊 统计',
            font_size=sp(20), bold=True,
            size_hint=(1, None), height=dp(45),
            color=hex_color(COLORS['text'])
        )
        layout.add_widget(title)

        self.scroll = ScrollView()
        self.content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(10),
            padding=(0, dp(5))
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        layout.add_widget(self.scroll)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def refresh(self):
        """刷新统计"""
        self.content.clear_widgets()
        app = App.get_running_app()
        stats = app.manager.get_statistics()

        if stats['total'] == 0:
            self.content.add_widget(Label(
                text='暂无数据',
                size_hint=(1, None), height=dp(150),
                halign='center', font_size=sp(15),
                color=hex_color(COLORS['gray'])
            ))
            return

        # 统计网格
        grid = GridLayout(cols=2, size_hint=(1, None), spacing=dp(8))
        grid.bind(minimum_height=grid.setter('height'))

        items = [
            ('总联系人', stats['total'], 'primary'),
            ('有手机号', stats['with_phone'], 'success'),
            ('已逾期', stats['overdue'], 'danger'),
            ('今日需联系', stats['today_due'], 'warning'),
            ('即将需要', stats['upcoming'], 'primary'),
            ('无手机号', stats['without_phone'], 'gray'),
        ]

        for label, value, color in items:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(8))
            from kivy.graphics import Color, Rectangle
            with card.canvas.before:
                Color(*hex_color(COLORS['white']))
                bg = Rectangle(pos=card.pos, size=card.size)

            def make_update(c):
                def update(instance, value):
                    c.pos = instance.pos
                    c.size = instance.size
                return update
            card.bind(pos=make_update(bg), size=make_update(bg))

            card.add_widget(Label(
                text=str(value),
                font_size=sp(22), bold=True,
                color=hex_color(COLORS[color if color != 'gray' else 'gray'])
            ))
            card.add_widget(Label(
                text=label,
                font_size=sp(12),
                color=hex_color(COLORS['gray'])
            ))
            grid.add_widget(card)

        self.content.add_widget(grid)

        # 间隔分布
        self.content.add_widget(Label(
            text='联系间隔分布',
            size_hint=(1, None), height=dp(35),
            font_size=sp(15), bold=True,
            halign='left', color=hex_color(COLORS['text'])
        ))

        for interval, count in sorted(stats['interval_dist'].items()):
            row = BoxLayout(size_hint=(1, None), height=dp(30))
            row.add_widget(Label(
                text=f'每 {interval} 天',
                size_hint=(0.4, 1), font_size=sp(13),
                color=hex_color(COLORS['text'])
            ))
            row.add_widget(Label(
                text=f'{count} 人',
                size_hint=(0.6, 1), font_size=sp(13),
                color=hex_color(COLORS['primary']),
                halign='right'
            ))
            self.content.add_widget(row)


class Toast(Label):
    """Toast 提示组件"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.graphics import Color, RoundedRectangle
        with self.canvas.before:
            Color(*hex_color('#000000', 0.8))
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ContactApp(App):
    """主应用"""

    def build(self):
        self.title = '联系人提醒'
        Window.clearcolor = hex_color(COLORS['bg'])

        # 数据目录（Android 上持久化保存）
        data_dir = self.user_data_dir
        self.manager = ContactManager(data_dir)

        # 屏幕管理器
        self.sm = ScreenManager()

        self.today_screen = TodayScreen(name='today')
        self.contacts_screen = ContactsScreen(name='contacts')
        self.add_screen = AddScreen(name='add')
        self.edit_screen = EditScreen(name='edit')
        self.stats_screen = StatsScreen(name='stats')

        self.sm.add_widget(self.today_screen)
        self.sm.add_widget(self.contacts_screen)
        self.sm.add_widget(self.add_screen)
        self.sm.add_widget(self.edit_screen)
        self.sm.add_widget(self.stats_screen)

        # 底部导航
        root = BoxLayout(orientation='vertical')
        root.add_widget(self.sm)

        nav = BoxLayout(size_hint=(1, None), height=dp(58), spacing=dp(2))
        from kivy.graphics import Color, Rectangle
        with nav.canvas.before:
            Color(*hex_color(COLORS['white']))
            nav_bg = Rectangle(pos=nav.pos, size=nav.size)

        def update_nav(instance, value):
            nav_bg.pos = instance.pos
            nav_bg.size = instance.size
        nav.bind(pos=update_nav, size=update_nav)

        nav_items = [
            ('📅', '今日', 'today'),
            ('👥', '联系人', 'contacts'),
            ('➕', '添加', 'add'),
            ('📊', '统计', 'stats'),
        ]

        self.nav_buttons = {}
        for icon, label, screen_name in nav_items:
            btn = Button(
                text=f'{icon}\n{label}',
                font_size=sp(11),
                background_normal='',
                background_color=hex_color(COLORS['white']),
                color=hex_color(COLORS['gray'])
            )
            btn.bind(on_release=lambda x, s=screen_name: self.switch_screen(s))
            nav.add_widget(btn)
            self.nav_buttons[screen_name] = btn

        root.add_widget(nav)

        # Toast
        self.toast = Toast(
            text='',
            size_hint=(None, None),
            size=(dp(200), dp(45)),
            pos_hint={'center_x': 0.5, 'y': 0.1},
            opacity=0
        )
        root.add_widget(self.toast)

        # 初始加载
        Clock.schedule_once(lambda dt: self.initial_load(), 0.1)

        return root

    def initial_load(self):
        """初始化加载"""
        self.today_screen.refresh()
        self.update_nav('today')

    def switch_screen(self, name):
        """切换页面"""
        self.sm.current = name
        if name == 'today':
            self.today_screen.refresh()
        elif name == 'contacts':
            self.contacts_screen.refresh()
        elif name == 'stats':
            self.stats_screen.refresh()
        self.update_nav(name)

    def update_nav(self, current):
        """更新底部导航高亮"""
        for name, btn in self.nav_buttons.items():
            if name == current:
                btn.color = hex_color(COLORS['primary'])
            else:
                btn.color = hex_color(COLORS['gray'])

    def show_toast(self, message):
        """显示 Toast 提示"""
        self.toast.text = message
        self.toast.opacity = 1

        def hide(dt):
            self.toast.opacity = 0

        Clock.schedule_once(hide, 1.8)

    def export_to_shared(self):
        """导出数据到共享目录（Android）"""
        import json
        from datetime import datetime

        data = {
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': len(self.manager.contacts),
            'contacts': self.manager.contacts
        }

        # 尝试写入 Android 的共享目录
        try:
            from android.storage import primary_external_storage_path
            shared_dir = primary_external_storage_path()
            filepath = os.path.join(shared_dir, 'Documents',
                                   f'contacts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        except Exception:
            # 桌面调试环境
            filepath = f'contacts_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath


if __name__ == '__main__':
    ContactApp().run()