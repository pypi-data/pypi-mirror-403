# 安装: pip install httpx pydantic
from typing import Optional, List
from pydantic import BaseModel
import httpx
from functools import wraps
import asyncio
import inspect

# 定义数据模型
class User(BaseModel):
    id: int
    name: str
    email: str

class Post(BaseModel):
    id: int
    title: str
    content: str

# 声明式客户端装饰器
def service_client(base_url: str):
    def decorator(cls):
        class ServiceClient:
            def __init__(self):
                self.client = httpx.AsyncClient(base_url=base_url)
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, *args):
                await self.client.aclose()
        
        for name, method in cls.__dict__.items():
            if callable(method) and not name.startswith('_'):
                setattr(ServiceClient, name, method)
        
        return ServiceClient
    return decorator

# 定义服务接口
@service_client("https://jsonplaceholder.typicode.com")
class UserService:
    """用户服务客户端"""
    
    async def get_user(self, user_id: int) -> User:
        """获取用户信息"""
        response = await self.client.get(f"/users/{user_id}")
        response.raise_for_status()
        return User(**response.json())
    
    async def get_users(self) -> List[User]:
        """获取所有用户"""
        response = await self.client.get("/users")
        response.raise_for_status()
        return [User(**item) for item in response.json()]
    
    async def create_user(self, user: User) -> User:
        """创建用户"""
        response = await self.client.post("/users", json=user.dict())
        response.raise_for_status()
        return User(**response.json())

# 使用示例
async def main():
    async with UserService() as client:
        # 调用声明式方法
        user = await client.get_user(1)
        print(user)
        
        users = await client.get_users()
        print(f"Total users: {len(users)}")

if __name__ == "__main__":
  r = httpx.get("https://www.baidu.com")
  print(r.text)