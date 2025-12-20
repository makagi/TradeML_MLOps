# -*- coding: utf-8 -*-
"""コンポーネントレジストリ - すべての利用可能なコンポーネントを管理"""
from typing import Dict, Callable, Any
from kfp import dsl


class ComponentRegistry:
    """パイプラインコンポーネントの登録と取得を管理"""
    
    def __init__(self):
        self._components: Dict[str, Callable] = {}
    
    def register(self, name: str, component: Callable):
        """コンポーネントを登録
        
        Args:
            name: コンポーネント名（YAML設定のtypeと対応）
            component: KFP componentデコレータが適用された関数
        """
        if name in self._components:
            print(f"Warning: Component '{name}' is being overwritten")
        self._components[name] = component
        print(f"[OK] Registered component: {name}")
    
    def get(self, name: str) -> Callable:
        """コンポーネントを取得
        
        Args:
            name: コンポーネント名
            
        Returns:
            コンポーネント関数
            
        Raises:
            KeyError: コンポーネントが見つからない場合
        """
        if name not in self._components:
            available = ', '.join(self._components.keys())
            raise KeyError(
                f"Component '{name}' not found. "
                f"Available components: {available}"
            )
        return self._components[name]
    
    def list_components(self) -> Dict[str, str]:
        """登録済みコンポーネント一覧を取得
        
        Returns:
            {コンポーネント名: 説明} の辞書
        """
        return {
            name: comp.__doc__ or "No description"
            for name, comp in self._components.items()
        }
    
    def is_registered(self, name: str) -> bool:
        """コンポーネントが登録されているかチェック
        
        Args:
            name: コンポーネント名
            
        Returns:
            登録されていればTrue
        """
        return name in self._components


# グローバルレジストリインスタンス
_registry = ComponentRegistry()


def register_component(name: str):
    """コンポーネント登録デコレータ
    
    使用例:
        @register_component('my_component')
        @dsl.component(base_image="python:3.9")
        def my_component_func(param: str):
            pass
    """
    def decorator(component: Callable) -> Callable:
        _registry.register(name, component)
        return component
    return decorator


def get_component(name: str) -> Callable:
    """コンポーネントを取得（グローバルレジストリから）"""
    return _registry.get(name)


def list_all_components() -> Dict[str, str]:
    """すべての登録済みコンポーネントをリスト"""
    return _registry.list_components()


def get_registry() -> ComponentRegistry:
    """グローバルレジストリインスタンスを取得"""
    return _registry


if __name__ == "__main__":
    # テスト実行
    print("=== Component Registry Test ===")
    
    # ダミーコンポーネントを登録
    @register_component('test_component')
    @dsl.component(base_image="python:3.9")
    def test_component(input_data: str) -> str:
        """テスト用コンポーネント"""
        return input_data
    
    # 登録済みコンポーネントをリスト
    print("\nRegistered components:")
    for name, desc in list_all_components().items():
        print(f"  - {name}: {desc}")
    
    # コンポーネントを取得
    comp = get_component('test_component')
    print(f"\nRetrieved component: {comp.__name__}")
