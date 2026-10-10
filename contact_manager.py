#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
联系人数据管理 - Kivy版
数据存储使用 JSON 文件，位置在 App 私有目录
"""

import json
import os
import random
from datetime import datetime, timedelta


class ContactManager:
    """联系人管理器"""

    def __init__(self, data_dir):
        """
        :param data_dir: 数据存储目录（Kivy 的 user_data_dir）
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.data_file = os.path.join(self.data_dir, 'contacts.json')
        self.contacts = []
        self.load_data()

    # ============ 数据读写 ============

    def load_data(self):
        """加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.contacts = data.get('contacts', [])
            except Exception:
                self.contacts = []
        else:
            self.contacts = []
            self.save_data()

    def save_data(self):
        """保存数据"""
        try:
            data = {
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total': len(self.contacts),
                'contacts': self.contacts
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存失败: {e}")

    # ============ 联系人增删改查 ============

    def add_contact(self, name, interval=7, phone='', remark=''):
        """添加联系人"""
        # 检查重名
        for c in self.contacts:
            if c['name'] == name:
                return False, f'联系人「{name}」已存在'

        contact = {
            'id': self._new_id(),
            'name': name,
            'phone': phone,
            'remark': remark,
            'interval': interval,
            'last_contact': datetime.now().strftime('%Y-%m-%d'),
            'source': 'manual',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.contacts.append(contact)
        self.save_data()
        return True, '添加成功'

    def update_contact(self, contact_id, **kwargs):
        """更新联系人"""
        for c in self.contacts:
            if c['id'] == contact_id:
                for key in ['name', 'phone', 'remark', 'interval']:
                    if key in kwargs:
                        c[key] = kwargs[key]
                self.save_data()
                return True, '更新成功'
        return False, '联系人不存在'

    def delete_contact(self, contact_id):
        """删除联系人"""
        for i, c in enumerate(self.contacts):
            if c['id'] == contact_id:
                del self.contacts[i]
                self.save_data()
                return True, '删除成功'
        return False, '联系人不存在'

    def get_contact(self, contact_id):
        """获取单个联系人"""
        for c in self.contacts:
            if c['id'] == contact_id:
                return c
        return None

    def mark_contacted(self, contact_id):
        """标记已联系"""
        for c in self.contacts:
            if c['id'] == contact_id:
                c['last_contact'] = datetime.now().strftime('%Y-%m-%d')
                self.save_data()
                return True
        return False

    def _new_id(self):
        """生成新ID"""
        if not self.contacts:
            return 1
        return max(c['id'] for c in self.contacts) + 1

    # ============ 查询与统计 ============

    def get_all_contacts(self):
        """获取所有联系人"""
        return self.contacts

    def search_contacts(self, keyword):
        """搜索联系人"""
        if not keyword:
            return self.contacts
        kw = keyword.lower()
        result = []
        for c in self.contacts:
            if (kw in c['name'].lower() or
                kw in c.get('phone', '').lower() or
                kw in c.get('remark', '').lower()):
                result.append(c)
        return result

    def get_next_contact_date(self, contact):
        """计算下次联系日期"""
        last = datetime.strptime(contact['last_contact'], '%Y-%m-%d')
        next_date = last + timedelta(days=contact['interval'])
        return next_date.strftime('%Y-%m-%d')

    def get_contact_status(self, contact):
        """获取联系人状态"""
        today = datetime.now().strftime('%Y-%m-%d')
        next_date = self.get_next_contact_date(contact)

        if next_date < today:
            return 'overdue'
        elif next_date == today:
            return 'today'
        else:
            days_left = (datetime.strptime(next_date, '%Y-%m-%d') - datetime.now()).days
            if days_left <= 3:
                return 'upcoming'
            return 'normal'

    def get_overdue_days(self, contact):
        """获取逾期天数"""
        today = datetime.now().strftime('%Y-%m-%d')
        next_date = self.get_next_contact_date(contact)
        if next_date < today:
            return (datetime.strptime(today, '%Y-%m-%d') -
                    datetime.strptime(next_date, '%Y-%m-%d')).days
        return 0

    def get_today_contacts(self):
        """获取今日需联系和已逾期的联系人"""
        need_contact = []
        overdue = []

        for c in self.contacts:
            status = self.get_contact_status(c)
            if status == 'overdue':
                overdue.append(c)
            elif status == 'today':
                need_contact.append(c)

        # 逾期按天数降序
        overdue.sort(key=lambda x: self.get_overdue_days(x), reverse=True)
        return need_contact, overdue

    def get_statistics(self):
        """获取统计信息"""
        total = len(self.contacts)
        with_phone = sum(1 for c in self.contacts if c.get('phone'))

        interval_dist = {}
        for c in self.contacts:
            iv = c['interval']
            interval_dist[iv] = interval_dist.get(iv, 0) + 1

        need_contact, overdue = self.get_today_contacts()

        # 未来7天即将需要联系
        upcoming = 0
        today = datetime.now()
        seven_days_later = today + timedelta(days=7)
        for c in self.contacts:
            next_date = datetime.strptime(self.get_next_contact_date(c), '%Y-%m-%d')
            if today < next_date <= seven_days_later:
                upcoming += 1

        return {
            'total': total,
            'with_phone': with_phone,
            'without_phone': total - with_phone,
            'overdue': len(overdue),
            'today_due': len(need_contact),
            'upcoming': upcoming,
            'interval_dist': interval_dist
        }

    def get_upcoming_contacts(self, days=7):
        """获取未来N天需要联系的联系人"""
        today = datetime.now()
        later = today + timedelta(days=days)
        result = []
        for c in self.contacts:
            next_date = datetime.strptime(self.get_next_contact_date(c), '%Y-%m-%d')
            if today < next_date <= later:
                result.append(c)
        result.sort(key=lambda x: self.get_next_contact_date(x))
        return result