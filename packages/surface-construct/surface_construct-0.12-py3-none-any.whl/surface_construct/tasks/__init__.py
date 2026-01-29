"""
所有具体业务的调用都在 Task 中，包含任务类别
* 表面终结的生成和评价 termination
* 位点的分析 site_analysis
* 构象分析 conf_analysis
* 位点的采样 site_sampling

基本的使用逻辑是
1. 产生实例 obj，
2. 实例赋值，（非必须）
3. obj.run 运行任务
4. 分析和作图
"""
from .sitesampling import SurfaceSiteSampleTask
from .afm import AFMTask