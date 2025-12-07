# HSLS:09（含 Second Follow-up 2017 PETS）代码本速览

面向：学生主样本（Base Year/F1/PETS）、家长、学校/课程记录与后续链接；字段来源于 `codebook/Codebook_HSLS_17_PETS.txt`。

## 标识与抽样
- 样本与权重：`W1STUDENT`、`W2STUDENT`、`W4STUDENT` 等主权重；对应 BRR/复制权重见补充文件（如 `psstudent_brr_ruf.dat`）。
- 个体标识：学生 ID（文件内隐含字段）、学校 ID 及 NCES 关联 `X1NCESID`，学校部门/控制 `X1CONTROL`（公、天主/其他私立）。
- 抽样状态：各轮应答/缺失状态 `X1SQSTAT`、`X2SQSTAT`、`X4MATCHATMPT` 等。

## 基本人口学
- 性别：`X1SEX`（后续轮次对应 `X2SEX` 等），第二随访性别身份 `X4GENDERID`（含抑制码 -5）。
- 出生时间：`X1STDOB`（YYYYMM，若年份底/顶码），或问卷分项 `S1BIRTHMON`、`S1BIRTHYR`。
- 移民背景：`X4IMGEN`（移民代际，基于本人/父母出生地）。
- 种族/族裔：`X1RACE`（合成），子项如 `X1HISPANIC`、`X1WHITE` 等。

## 家庭背景与社会经济
- 家庭收入：`X1FAMINCOME`（分组，缺失/抑制见代码本）。
- 家长教育：`X1PAREDU`（父母/监护人最高教育，派生自 `X1PAR1EDU`、`X1PAR2EDU`），后续轮次有 `X2PAREDU`。
- 家长职业：O*NET 2 位/6 位码 `X1PAR1OCC2`、`X1PAR2OCC2`（及派生母亲/父亲职业 `X1MOMOCC2`、`X1DADOCC2`），第二轮 `X2PAR1OCC2` 等；需映射至 ISCO/ISEI 另行转换。
- SES 综合：`X1SES`（教育/职业/收入综合指数，含 5 次插补均值），带有缺失/插补标记 `X1SES_IM`；城镇性版本 `X1SES_U`；后续轮次 `X2SES` 等。
- 语言（部分抑制）：`X1NATIVELANG`、`X1DUALLANG` 等，抑制码 -5/-9 需过滤。

## 学业成绩与课程
- 认知：数学 theta `X1TXMTH`（及多重插补 `X1TXMTH1-5`）、标准化 T 分 `X1TXMTSCOR`；后续轮次对应 `X2TXMTH` 等。
- 课程与学分：课程选修/学分记录（如 `X3CRS_MATH`，`X3GPA_MATH`，AP/课程模式标识），取决于记录文件。
- 成绩/测评附加：标准化分数、退出/毕业状态 `X2ENROLSTAT` 等。

## 学习态度、动机与心理量表
- 数学自我效能：`X1MTHEFF`（后续 `X2MTHEFF`），输入为 S1MTESTS 等。
- 数学兴趣/乐趣：`X1MTHINT`（后续有对应）。
- 科学效用：`X1SCIUTI`。
- 归属感/学校氛围：`X1SCHOOLBEL`。
- 学业期望/教育规划：相关单项/量表（如 `S1EXPECT` 类条目，视文件）。

## ICT 使用与信息行为
- 网络/技术信息搜索：`S1WEBINFO`（是否用网络查计算机技术信息）。
- 电脑/课程相关条目：课程/学分中有计算机科学学分 `X3` 记录等。

## 家长问卷（选摘）
- 家长关系与教育支持：`X1P1RELATION`、`X1P2RELATION`，作业帮助/能力如 `P1MTHHWEFF`。
- 父母出生地/移民：`P1USBORN*`、`P2USBORN*`（用于生成 `X4IMGEN`）。

## 学校与环境
- 学校部门/控制：`X1CONTROL`（公、天主/其他私立）；后续 `X2CONTROL`、`X3CONTROL`、`X4CONTROL`。
- 城镇性：`X1LOCALE`（City/Suburb/Town/Rural），后续 `X2LOCALE`。
- 学校层权重与链接：见 NCES/CCD/PSS 关联字段。

## 缺失与特殊值
- 负值编码：-9（缺失）、-8（单元缺访）、-7（不适用）、-5（抑制）等，分析前需按代码本处理。
- 插补标记：诸如 `_IM` 结尾字段标识插补状态。

> 提示：跨国/跨资料对比时，HSLS 仅代表美国 9 年级起始队列；使用相应权重（如 `W1STUDENT`）并结合插补/抑制码过滤；O*NET 职业码需外部映射后才能与 PISA ISCO/ISEI 直接比较。指标命名前缀：X1=Base Year，X2=First Follow-up，X4=Second Follow-up (PETS)。***
